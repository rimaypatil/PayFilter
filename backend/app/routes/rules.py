"""Merchant rules configuration routes (GET/PUT /rules)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.db.models import AuthenticatedUser, RulesConfig
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.dependencies import (
    get_audit_repo,
    get_current_user,
    get_rules_repo,
    require_role,
)

logger = logging.getLogger("payfilter.routes.rules")
router = APIRouter(prefix="/rules", tags=["Rules"])


class UpdateRulesRequest(BaseModel):
    """Payload to update merchant risk thresholds and caps."""

    max_amount_per_order: Optional[float] = Field(
        default=None, gt=0, description="Hard cap on single order amount"
    )
    max_transactions_per_minute: Optional[int] = Field(
        default=None, gt=0, description="Max velocity per minute before hard block"
    )
    category_limits: Optional[Dict[str, float]] = Field(
        default=None, description="Per-category amount limits"
    )


@router.get(
    "",
    response_model=RulesConfig,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current merchant risk rules configuration",
)
def get_merchant_rules(
    current_user: AuthenticatedUser = Depends(require_role("analyst")),
    rules_repo: RulesRepository = Depends(get_rules_repo),
) -> RulesConfig:
    """Returns the rules config for the calling user's merchant.

    # FRONTEND: rules settings tab calls this in Phase 4
    """
    return rules_repo.get_rules_config(current_user.merchant_id)


@router.put(
    "",
    response_model=RulesConfig,
    status_code=status.HTTP_200_OK,
    summary="Update merchant risk rules configuration (Admin only)",
)
def update_merchant_rules(
    request: UpdateRulesRequest,
    current_user: AuthenticatedUser = Depends(require_role("admin")),
    rules_repo: RulesRepository = Depends(get_rules_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> RulesConfig:
    """Updates merchant threshold limits and records audit log.

    # FRONTEND: save rules button calls this in Phase 4
    """
    updated = rules_repo.update_rules_config(
        merchant_id=current_user.merchant_id,
        max_amount_per_order=request.max_amount_per_order,
        max_transactions_per_minute=request.max_transactions_per_minute,
        category_limits=request.category_limits,
    )

    # Record audit event
    audit_repo.append_audit_entry(
        merchant_id=current_user.merchant_id,
        action="rules_config_updated",
        actor=current_user.user_id,
    )

    logger.info(f"Rules updated for merchant {current_user.merchant_id} by {current_user.user_id}")
    return updated
