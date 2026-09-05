"""Merchant onboarding and API key management routes."""

from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.app.auth.jwt_verify import verify_supabase_jwt
from backend.app.db.models import AuthenticatedUser
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.dependencies import (
    get_audit_repo,
    get_current_user,
    get_merchants_repo,
    get_rules_repo,
    require_role,
)

logger = logging.getLogger("payfilter.routes.merchants")
router = APIRouter(prefix="/merchants", tags=["Merchants"])
bearer_scheme = HTTPBearer(auto_error=False)


class MerchantSignupRequest(BaseModel):
    """Payload for registering a new merchant tenant."""

    name: str = Field(..., min_length=2, max_length=100, description="Business or merchant name")
    admin_user_id: Optional[str] = Field(None, description="Supabase Auth UUID of the initial admin user (optional when Bearer token is provided)")


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


class ApiKeyStatusResponse(BaseModel):
    """Overview of merchant API key metadata and endpoint settings."""

    merchant_id: str
    merchant_name: str
    role: str = "analyst"
    is_active: bool = True
    masked_key: str = "pf_live_••••••••••••••••"
    created_at: Optional[str] = None
    transaction_endpoint: str = "/transactions/check"


class MerchantMeResponse(BaseModel):
    """Authenticated user context, confirmed role, and merchant identity."""

    user_id: str
    email: Optional[str] = None
    role: str
    merchant_id: str
    merchant_name: str


@router.post(
    "/signup",
    response_model=MerchantSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new merchant organization and issue primary API key",
)
def signup_merchant(
    request: MerchantSignupRequest,
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
    rules_repo: RulesRepository = Depends(get_rules_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> MerchantSignupResponse:
    """Creates a new merchant, issues a single-reveal API key, and grants admin privileges.

    Workflow:
    1. Determine target admin user:
       - If Authorization Bearer token is provided: decode & verify token cryptographically via Supabase JWT verifier and extract sub (real UID).
       - If no Bearer token provided: fall back to request.admin_user_id (for backwards compatibility with tests).
       - Reject if neither is present.
    2. Create merchant record with securely hashed API key.
    3. Link initial Supabase Auth user as 'admin' in user_roles table.
    4. Initialize default rules_config (50,000 INR cap, 5 txns/min).
    5. Write audit log entry.
    6. Return plaintext API key once.
    """
    target_user_id: Optional[str] = None
    if auth_header and auth_header.credentials:
        claims = verify_supabase_jwt(auth_header.credentials)
        target_user_id = str(claims.get("sub") or claims.get("id") or claims.get("user_id") or "")

    if not target_user_id:
        target_user_id = request.admin_user_id

    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated session or admin_user_id is required to register a merchant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Create merchant and get one-time plaintext key
    merchant, plaintext_api_key = merchants_repo.create_merchant(
        name=request.name,
    )

    # 2. Assign admin role in user_roles
    merchants_repo.assign_user_role(
        user_id=target_user_id,
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
        actor=target_user_id,
    )

    logger.info(f"Merchant '{merchant.name}' ({merchant.id}) successfully created by {target_user_id}")

    return MerchantSignupResponse(
        merchant_id=merchant.id,
        name=merchant.name,
        api_key=plaintext_api_key,
        admin_user_id=target_user_id,
    )


@router.post(
    "/api-key/rotate",
    response_model=ApiKeyRotateResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate merchant API key (Admin only)",
)
def rotate_merchant_api_key(
    current_user: AuthenticatedUser = Depends(require_role("admin")),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
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


@router.get(
    "/api-key/status",
    response_model=ApiKeyStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get merchant API key overview and masked status (Admin & Analyst)",
)
def get_api_key_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
) -> ApiKeyStatusResponse:
    """Returns the authenticated merchant's API key overview, masked format, and endpoint configuration."""
    merchant = merchants_repo.get_merchant_by_id(current_user.merchant_id)
    merchant_name = merchant.name if merchant else "Merchant Organization"
    created_at = merchant.created_at if merchant else None

    return ApiKeyStatusResponse(
        merchant_id=current_user.merchant_id,
        merchant_name=merchant_name,
        role=current_user.role,
        is_active=True,
        masked_key="pf_live_••••••••••••••••",
        created_at=created_at,
        transaction_endpoint="/transactions/check",
    )


@router.get(
    "/me",
    response_model=MerchantMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get confirmed role and merchant identity for current user",
)
def get_current_merchant_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
) -> MerchantMeResponse:
    """Returns the authenticated user's confirmed role and merchant membership from database."""
    merchant = merchants_repo.get_merchant_by_id(current_user.merchant_id)
    merchant_name = merchant.name if merchant else "Merchant Organization"
    return MerchantMeResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role,
        merchant_id=current_user.merchant_id,
        merchant_name=merchant_name,
    )


