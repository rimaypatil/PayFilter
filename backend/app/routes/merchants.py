"""Merchant onboarding and API key management routes."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.db.models import AuthenticatedUser
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.dependencies import get_current_user, require_role

logger = logging.getLogger("payfilter.routes.merchants")
router = APIRouter(prefix="/merchants", tags=["Merchants"])


class MerchantSignupRequest(BaseModel):
    """Payload for registering a new merchant tenant."""

    name: str = Field(..., min_length=2, max_length=100, description="Business or merchant name")
    admin_user_id: str = Field(..., description="Supabase Auth UUID of the initial admin user")


class MerchantSignupResponse(BaseModel):
    """Merchant registration output with plaintext API key issued once."""

    merchant_id: str
    name: str
    api_key: str
    role: str = "admin"
    admin_user_id: str
    message: str = "Merchant created successfully. Store this API key securely; it cannot be viewed again."


class ApiKeyRotateResponse(BaseModel):
    """Output for API key rotation."""

    merchant_id: str
    api_key: str
    message: str = "API key rotated successfully. The previous key has been immediately invalidated."


@router.post(
    "/signup",
    response_model=MerchantSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new merchant organization and issue primary API key",
)
def signup_merchant(
    request: MerchantSignupRequest,
    merchants_repo: MerchantsRepository = Depends(MerchantsRepository),
    rules_repo: RulesRepository = Depends(RulesRepository),
    audit_repo: AuditRepository = Depends(AuditRepository),
) -> MerchantSignupResponse:
    """Creates a new merchant, issues a single-reveal API key, and grants admin privileges.

    Workflow:
    1. Create merchant record with securely hashed API key.
    2. Link initial Supabase Auth user as 'admin' in user_roles table.
    3. Initialize default rules_config (50,000 INR cap, 5 txns/min).
    4. Write audit log entry.
    5. Return plaintext API key once.

    # FRONTEND: signup form calls this in Phase 4
    """
    # 1. Create merchant and get one-time plaintext key
    merchant, plaintext_api_key = merchants_repo.create_merchant(
        name=request.name,
    )

    # 2. Assign admin role in user_roles
    merchants_repo.assign_user_role(
        user_id=request.admin_user_id,
        merchant_id=merchant.id,
        role="admin",
    )

    # 3. Initialize default rules config
    rules_repo.upsert_rules_config(
        merchant_id=merchant.id,
        max_amount_per_order=50000.0,
        max_transactions_per_minute=5,
    )

    # 4. Record audit event
    audit_repo.append_audit_entry(
        merchant_id=merchant.id,
        action="merchant_registered",
        actor=request.admin_user_id,
    )

    logger.info(f"Merchant '{merchant.name}' ({merchant.id}) successfully created by {request.admin_user_id}")

    return MerchantSignupResponse(
        merchant_id=merchant.id,
        name=merchant.name,
        api_key=plaintext_api_key,
        admin_user_id=request.admin_user_id,
    )


@router.post(
    "/api-key/rotate",
    response_model=ApiKeyRotateResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate merchant API key (Admin only)",
)
def rotate_merchant_api_key(
    current_user: AuthenticatedUser = Depends(require_role("admin")),
    merchants_repo: MerchantsRepository = Depends(MerchantsRepository),
    audit_repo: AuditRepository = Depends(AuditRepository),
) -> ApiKeyRotateResponse:
    """Invalidates current API key hash and returns newly generated plaintext key.

    # FRONTEND: settings developer tab calls this in Phase 4
    """
    new_plaintext_key = merchants_repo.rotate_api_key(current_user.merchant_id)

    # Record audit event
    audit_repo.append_audit_entry(
        merchant_id=current_user.merchant_id,
        action="api_key_rotated",
        actor=current_user.user_id,
    )

    logger.info(f"API key rotated for merchant {current_user.merchant_id} by {current_user.user_id}")

    return ApiKeyRotateResponse(
        merchant_id=current_user.merchant_id,
        api_key=new_plaintext_key,
    )
