"""Kill switch management routes with step-up authentication."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.auth.step_up import generate_step_up_code, validate_and_consume_step_up_code
from backend.app.db.models import AuthenticatedUser, KillSwitchState
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.dependencies import get_current_user, require_role

logger = logging.getLogger("payfilter.routes.kill_switch")
router = APIRouter(prefix="/kill-switch", tags=["Kill Switch"])


class KillSwitchRequestResponse(BaseModel):
    """Response containing short-lived step-up OTP code."""

    code: str = Field(..., description="6-digit step-up verification code")
    expires_at: datetime
    action: str = "kill_switch"
    message: str = (
        "Step-up verification code issued. In production this would be sent via SMS/Email; "
        "for this phase, it is returned directly in the response."
    )


class KillSwitchConfirmRequest(BaseModel):
    """Payload to toggle the merchant kill switch."""

    code: str = Field(..., min_length=6, max_length=6, description="6-digit step-up verification code")
    is_active: bool = Field(..., description="True to activate kill switch (halt payments), False to resume")
    reason: Optional[str] = Field(default="Manual emergency trigger", description="Justification for kill switch change")


class KillSwitchConfirmResponse(BaseModel):
    """Result of kill switch execution."""

    merchant_id: str
    is_active: bool
    status: str
    activated_by: str
    audit_log_id: str


@router.post(
    "/request",
    response_model=KillSwitchRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a short-lived step-up verification code (Admin only)",
)
def request_kill_switch_code(
    current_user: AuthenticatedUser = Depends(require_role("admin")),
) -> KillSwitchRequestResponse:
    """Issues a 5-minute one-time step-up code for the authenticated admin.

    # FRONTEND: dashboard kill switch modal calls this to initiate step-up in Phase 4
    """
    code, expires_at = generate_step_up_code(
        user_id=current_user.user_id,
        action="kill_switch",
        expiry_seconds=300,
    )
    return KillSwitchRequestResponse(
        code=code,
        expires_at=expires_at,
        action="kill_switch",
    )


@router.post(
    "/confirm",
    response_model=KillSwitchConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm and execute kill switch state change using step-up code (Admin only)",
)
def confirm_kill_switch(
    request: KillSwitchConfirmRequest,
    current_user: AuthenticatedUser = Depends(require_role("admin")),
    merchants_repo: MerchantsRepository = Depends(MerchantsRepository),
    audit_repo: AuditRepository = Depends(AuditRepository),
) -> KillSwitchConfirmResponse:
    """Executes the kill switch toggle only upon successful step-up code validation.

    Requires:
    1. Valid Admin session token.
    2. Valid unexpired step-up OTP issued by /kill-switch/request.
    """
    # 1. Validate and consume step-up OTP (raises 403 on failure)
    validate_and_consume_step_up_code(
        user_id=current_user.user_id,
        code=request.code,
        action="kill_switch",
    )

    # 2. Update merchant kill switch state
    state = merchants_repo.set_kill_switch_state(
        merchant_id=current_user.merchant_id,
        is_active=request.is_active,
        activated_by=current_user.user_id,
        reason=request.reason,
    )

    # 3. Append immutable audit trail entry
    audit_action = "kill_switch_activated" if request.is_active else "kill_switch_deactivated"
    audit_entry = audit_repo.append_audit_entry(
        merchant_id=current_user.merchant_id,
        action=f"{audit_action}:{request.reason}",
        transaction_id=None,
        actor=current_user.user_id,
    )

    logger.warning(
        f"Kill switch {audit_action} for merchant {current_user.merchant_id} by {current_user.user_id}"
    )

    return KillSwitchConfirmResponse(
        merchant_id=current_user.merchant_id,
        is_active=state.is_active,
        status="ACTIVE (ALL TRANSACTIONS BLOCKED)" if state.is_active else "INACTIVE (NORMAL OPERATIONS)",
        activated_by=current_user.user_id,
        audit_log_id=audit_entry.id or "",
    )


@router.get(
    "/status",
    response_model=KillSwitchState,
    status_code=status.HTTP_200_OK,
    summary="Query current kill switch status for merchant",
)
def get_kill_switch_status(
    current_user: AuthenticatedUser = Depends(require_role("analyst")),
    merchants_repo: MerchantsRepository = Depends(MerchantsRepository),
) -> KillSwitchState:
    """Returns the kill switch status for the calling user's merchant."""
    return merchants_repo.get_kill_switch_state(current_user.merchant_id)
