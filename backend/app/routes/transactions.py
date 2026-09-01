"""Transaction scoring route (POST /transactions/check) with API Key Auth & Kill Switch check."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

# Root proxy imports from Phase 1
from ml.features import extract_single_transaction_features
from backend.app.db.models import RulesConfig
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.dependencies import require_api_key
from backend.app.risk_engine.idempotency import IdempotencyChecker
from backend.app.risk_engine.model import MLModelManager, get_model_manager
from backend.app.risk_engine.rules import RuleEngine
from backend.app.risk_engine.scorer import RiskScorer
from backend.app.schemas import TransactionCheckRequest, TransactionCheckResponse

from backend.app.integrations.claude_client import ClaudeClient, get_claude_client
from backend.app.integrations.razorpay_client import RazorpayClient, get_razorpay_client

logger = logging.getLogger("payfilter.routes.transactions")
router = APIRouter(prefix="/transactions", tags=["Transactions"])


# Dependency providers
def get_txns_repo() -> TransactionsRepository:
    return TransactionsRepository()


def get_audit_repo() -> AuditRepository:
    return AuditRepository()


def get_rules_repo() -> RulesRepository:
    return RulesRepository()


def get_merchants_repo() -> MerchantsRepository:
    return MerchantsRepository()


def get_risk_scorer() -> RiskScorer:
    return RiskScorer()


@router.post(
    "/check",
    response_model=TransactionCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate transaction risk and return decision (Requires Merchant API Key)",
)
def check_transaction(
    request: TransactionCheckRequest,
    auth_merchant_id: str = Depends(require_api_key),
    txns_repo: TransactionsRepository = Depends(get_txns_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    rules_repo: RulesRepository = Depends(get_rules_repo),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
    scorer: RiskScorer = Depends(get_risk_scorer),
    model_manager: MLModelManager = Depends(get_model_manager),
    rzp_client: RazorpayClient = Depends(get_razorpay_client),
    claude_client: ClaudeClient = Depends(get_claude_client),
) -> TransactionCheckResponse:
    """Evaluates an incoming AI-agent payment transaction.

    Workflow:
    1. Authenticate calling merchant via API key (X-API-Key).
    2. Enforce tenant ownership (request.merchant_id must match authenticated merchant).
    3. Check Kill Switch: If active, block transaction immediately and explain with Claude.
    4. Idempotency check: If transaction_id already exists, return stored decision.
    5. Customer history retrieval: Fetch past transactions strictly prior to t_curr.
    6. Feature extraction: Compute leakage-safe feature vector (features.py).
    7. Deterministic rules check: Evaluate merchant caps and velocity (rules.py).
    8. Scoring decision: Combine rules + ML anomaly model (scorer.py).
    9. Phase 5 Integrations:
       - If approved: Create real test-mode Razorpay order (failure-tolerant).
       - If held/blocked: Generate zero-PII plain-English explanation via Claude (timeout-tolerant).
    10. Database persistence: Write record to transactions table.
    11. Audit log append: Write cryptographically hash-chained entry to audit_log.
    12. Return structured decision with razorpay_order_id and explanation.
    """
    # 1. Enforce matching tenant ownership
    if request.merchant_id and request.merchant_id != auth_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant ID mismatch with authenticated API key.",
        )

    # 2. Check Merchant Kill Switch Status
    kill_switch = merchants_repo.get_kill_switch_state(auth_merchant_id)
    if kill_switch.is_active:
        logger.warning(f"Transaction {request.transaction_id} BLOCKED: Kill switch is ACTIVE for merchant {auth_merchant_id}")
        explanation = claude_client.explain_decision(
            {"decision": "blocked", "primary_driver": "kill_switch_activated", "rule_name": "emergency_kill_switch"},
            amount=request.amount,
            category=request.merchant_category,
            agent_type=request.agent_type,
        )
        reason_blocked = {
            "decision": "blocked",
            "primary_driver": "kill_switch_activated",
            "rule_name": "emergency_kill_switch",
            "rule_type": "hard",
            "rule_reason": kill_switch.reason or "Emergency kill switch active",
            "model_score": 1.0,
            "thresholds": {"hold": 0.45, "block": 0.70},
            "feature_drivers": ["merchant_kill_switch_engaged"],
            "explanation": explanation,
        }

        # Persist blocked transaction
        txn_record_data = {
            "id": request.transaction_id,
            "merchant_id": auth_merchant_id,
            "customer_id": request.customer_id,
            "amount": request.amount,
            "agent_type": request.agent_type,
            "status": "blocked",
            "risk_score": 1.0,
            "reason": reason_blocked,
            "model_version": model_manager.model_version,
            "razorpay_order_id": None,
            "created_at": request.timestamp.isoformat(),
        }
        persisted_txn = txns_repo.create_transaction(txn_record_data)

        # Audit entry
        audit_entry = audit_repo.append_audit_entry(
            merchant_id=auth_merchant_id,
            action="transaction_scored:blocked:kill_switch",
            transaction_id=request.transaction_id,
            actor="system",
            created_at=request.timestamp.isoformat(),
        )

        return TransactionCheckResponse(
            transaction_id=persisted_txn.id,
            status="blocked",
            risk_score=1.0,
            reason=reason_blocked,
            audit_log_id=audit_entry.id or "",
            razorpay_order_id=None,
        )

    # 3. Idempotency Check
    idempotency = IdempotencyChecker(transactions_repo=txns_repo)
    cached_result = idempotency.check_existing(request.transaction_id)
    if cached_result is not None:
        logger.info(f"Duplicate transaction_id '{request.transaction_id}' detected. Returning cached decision.")
        return cached_result

    # 4. Fetch Customer History strictly before current timestamp
    customer_history_df = txns_repo.get_customer_history(
        customer_id=request.customer_id,
        before_timestamp=request.timestamp,
        merchant_id=auth_merchant_id,
    )

    # 5. Extract Leakage-Safe Features
    txn_dict = {
        "id": request.transaction_id,
        "transaction_id": request.transaction_id,
        "merchant_id": auth_merchant_id,
        "customer_id": request.customer_id,
        "amount": request.amount,
        "timestamp": request.timestamp,
        "merchant_category": request.merchant_category,
        "agent_type": request.agent_type,
    }
    feature_vector = extract_single_transaction_features(
        current_txn=txn_dict,
        customer_history_df=customer_history_df,
    )

    # 6. Deterministic Rules Evaluation
    rules_config: RulesConfig = rules_repo.get_rules_config(auth_merchant_id)
    rule_engine = RuleEngine(transactions_repo=txns_repo)
    rule_result = rule_engine.evaluate_rules(request, rules_config)

    # 7. ML Scoring & Threshold Decision
    decision_status, risk_score, reason = scorer.score_transaction(
        rule_result=rule_result,
        features=feature_vector,
    )

    # 8. Phase 5 Integrations (Razorpay on Approve, Claude on Hold/Block)
    razorpay_order_id: Optional[str] = None
    if decision_status == "approved":
        razorpay_order_id = rzp_client.create_order(txn_dict)
        if not razorpay_order_id:
            audit_repo.append_audit_entry(
                merchant_id=auth_merchant_id,
                action="razorpay_order_creation_failed",
                transaction_id=request.transaction_id,
                actor="system",
                created_at=request.timestamp.isoformat(),
            )
    elif decision_status in ("held", "blocked"):
        # Zero-PII natural language explanation via Claude
        explanation = claude_client.explain_decision(
            reason,
            amount=request.amount,
            category=request.merchant_category,
            agent_type=request.agent_type,
        )
        reason["explanation"] = explanation

    # 9. Persist Transaction Record
    txn_record_data = {
        "id": request.transaction_id,
        "merchant_id": auth_merchant_id,
        "customer_id": request.customer_id,
        "amount": request.amount,
        "agent_type": request.agent_type,
        "status": decision_status,
        "risk_score": risk_score,
        "reason": reason,
        "model_version": model_manager.model_version,
        "razorpay_order_id": razorpay_order_id,
        "created_at": request.timestamp.isoformat(),
    }
    persisted_txn = txns_repo.create_transaction(txn_record_data)

    # 10. Append to Cryptographic Audit Chain
    audit_entry = audit_repo.append_audit_entry(
        merchant_id=auth_merchant_id,
        action=f"transaction_scored:{decision_status}",
        transaction_id=request.transaction_id,
        actor="system",
        created_at=request.timestamp.isoformat(),
    )

    # 11. Return Response
    return TransactionCheckResponse(
        transaction_id=persisted_txn.id,
        status=persisted_txn.status,  # type: ignore
        risk_score=persisted_txn.risk_score,
        reason=persisted_txn.reason,
        audit_log_id=audit_entry.id or "",
        razorpay_order_id=persisted_txn.razorpay_order_id,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List transactions for authenticated merchant with optional status filter",
)
def list_transactions(
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: Any = Depends(require_role("analyst")),
    txns_repo: TransactionsRepository = Depends(get_txns_repo),
):
    """Retrieves paginated transactions for the logged in merchant."""
    offset = (page - 1) * page_size
    records, total = txns_repo.get_transactions(
        merchant_id=current_user.merchant_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )
    return {
        "items": [r.model_dump() for r in records],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
