"""Human confirmation workflow route (POST /transactions/{id}/confirm)."""

from __future__ import annotations

import logging
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

# Root proxy import from Phase 1
from threshold_manager import AdaptiveThresholdManager
from backend.app.db.models import AuthenticatedUser, TransactionRecord
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.dependencies import get_current_user, require_role
from backend.app.risk_engine.scorer import RiskScorer

from backend.app.integrations.razorpay_client import RazorpayClient, get_razorpay_client

logger = logging.getLogger("payfilter.routes.confirmations")
router = APIRouter(prefix="/transactions", tags=["Confirmations"])

# Global threshold manager for live feedback adjustments
_global_threshold_mgr = AdaptiveThresholdManager(initial_threshold=0.45, max_change_rate=0.10)


class ConfirmationRequest(BaseModel):
    """Payload for human analyst confirmation."""

    decision: Literal["approve", "deny"] = Field(
        ...,
        description="Analyst resolution decision ('approve' converts to 'approved', 'deny' to 'blocked')",
    )


class ConfirmationResponse(BaseModel):
    """Result of human confirmation."""

    transaction_id: str
    status: str
    previous_status: str
    confirmed_by: str
    audit_log_id: str
    new_threshold: float
    razorpay_order_id: Optional[str] = None


@router.post(
    "/{id}/confirm",
    response_model=ConfirmationResponse,
    status_code=status.HTTP_200_OK,
    summary="Human analyst manual approval or denial of held transaction",
)
def confirm_held_transaction(
    id: str = Path(..., description="UUID of the transaction to confirm"),
    request: ConfirmationRequest = ...,
    current_user: AuthenticatedUser = Depends(require_role("analyst")),
    txns_repo: TransactionsRepository = Depends(TransactionsRepository),
    audit_repo: AuditRepository = Depends(AuditRepository),
    rzp_client: RazorpayClient = Depends(get_razorpay_client),
) -> ConfirmationResponse:
    """Resolves a transaction currently in 'held' state.

    Workflow:
    1. Verify transaction exists and belongs to caller's merchant_id (defense in depth).
    2. Enforce that transaction is currently in 'held' status (reject already approved/blocked).
    3. Update transaction status to 'approved' (if approve) or 'blocked' (if deny).
    4. If approved: Create test-mode Razorpay order for this confirmed transaction.
    5. Write immutable cryptographic audit log entry with action='confirmed_by_human'.
    6. Feed outcome into Phase 1 AdaptiveThresholdManager (respecting poisoning rate cap).
    7. Return updated transaction response.
    """
    # 1. Fetch transaction
    txn = txns_repo.get_transaction_by_id(id)
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{id}' not found.",
        )

    # 2. Verify merchant tenant ownership
    if txn.merchant_id != current_user.merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot confirm transaction belonging to another merchant.",
        )

    # 3. Check held status
    if txn.status != "held":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm transaction with status '{txn.status}'. Only 'held' transactions can be confirmed.",
        )

    # 4. Map decision to status
    new_status = "approved" if request.decision == "approve" else "blocked"
    reason_payload = {
        **(txn.reason if isinstance(txn.reason, dict) else {"details": txn.reason}),
        "human_confirmation": {
            "decision": request.decision,
            "resolved_status": new_status,
            "confirmed_by": current_user.user_id,
            "confirmed_by_email": current_user.email,
        },
    }

    # 5. Create Razorpay order if approved by human
    razorpay_order_id = None
    if new_status == "approved":
        razorpay_order_id = rzp_client.create_order(txn.model_dump())
        if not razorpay_order_id:
            audit_repo.append_audit_entry(
                merchant_id=current_user.merchant_id,
                action="razorpay_order_creation_failed_on_confirm",
                transaction_id=txn.id,
                actor=current_user.user_id,
            )

    # 6. Update database record
    updated_txn = txns_repo.update_transaction_status(
        transaction_id=txn.id,
        status=new_status,
        reason=reason_payload,
        razorpay_order_id=razorpay_order_id,
    )

    # 7. Append audit log
    audit_entry = audit_repo.append_audit_entry(
        merchant_id=current_user.merchant_id,
        action=f"confirmed_by_human:{new_status}",
        transaction_id=txn.id,
        actor=current_user.user_id,
    )

    # 8. Feed outcome into Phase 1 AdaptiveThresholdManager (with bounded drift cap)
    is_fraud_confirmed = request.decision == "deny"
    _global_threshold_mgr.update_threshold(is_fraud=is_fraud_confirmed)

    logger.info(
        f"Transaction {txn.id} confirmed as '{new_status}' by {current_user.user_id}. "
        f"New threshold: {_global_threshold_mgr.threshold:.4f}"
    )

    return ConfirmationResponse(
        transaction_id=txn.id,
        status=new_status,
        previous_status="held",
        confirmed_by=current_user.user_id,
        audit_log_id=audit_entry.id or "",
        new_threshold=round(_global_threshold_mgr.threshold, 4),
        razorpay_order_id=razorpay_order_id,
    )
