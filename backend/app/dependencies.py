"""FastAPI Dependency Providers for Authentication, RBAC, and Context Scoping."""

from __future__ import annotations

import logging
from typing import Callable, Optional
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.auth.api_key_auth import verify_merchant_api_key
from backend.app.auth.jwt_verify import verify_supabase_jwt
from backend.app.auth.permissions import check_role_permission
from backend.app.auth.step_up import validate_and_consume_step_up_code
from backend.app.db.models import AuthenticatedUser
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository

logger = logging.getLogger("payfilter.dependencies")

bearer_scheme = HTTPBearer(auto_error=False)


def get_merchants_repo() -> MerchantsRepository:
    """Dependency returning MerchantsRepository instance."""
    return MerchantsRepository()


def get_rules_repo() -> RulesRepository:
    """Dependency returning RulesRepository instance."""
    return RulesRepository()


def get_audit_repo() -> AuditRepository:
    """Dependency returning AuditRepository instance."""
    return AuditRepository()


def get_txns_repo() -> TransactionsRepository:
    """Dependency returning TransactionsRepository instance."""
    return TransactionsRepository()


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
) -> AuthenticatedUser:
    """Authenticates the calling user via Supabase JWT and resolves role & merchant_id.

    Raises:
        HTTPException: 401 Unauthorized if missing/invalid token or unmapped user.
    """
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.credentials
    claims = verify_supabase_jwt(token)

    user_id = str(claims.get("sub") or claims.get("id") or claims.get("user_id") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required subject claim",
        )

    # 1. Check custom JWT claims (if explicitly set in app_metadata or user_metadata)
    app_metadata = claims.get("app_metadata", {})
    user_metadata = claims.get("user_metadata", {})
    merchant_id = (
        claims.get("merchant_id")
        or app_metadata.get("merchant_id")
        or user_metadata.get("merchant_id")
    )
    
    # Generic Supabase tokens contain role="authenticated"; only accept explicit application roles
    raw_role = (
        claims.get("user_role")
        or app_metadata.get("role")
        or user_metadata.get("role")
        or (claims.get("role") if claims.get("role") in ["admin", "analyst"] else None)
    )
    role = raw_role if raw_role in ["admin", "analyst"] else None

    # 2. Resolve merchant membership and role authoritatively from user_roles database table
    if not merchant_id or not role:
        try:
            user_role_entry = merchants_repo.get_user_role(user_id, auth_token=token)
            if user_role_entry:
                merchant_id = user_role_entry.merchant_id
                role = user_role_entry.role
        except Exception as e:
            logger.warning(f"Error resolving user_roles from database for {user_id}: {e}")

    # 3. Reject unmapped users strictly via RBAC
    if not merchant_id or not role or role not in ["admin", "analyst"]:
        logger.warning(f"Authenticated user {user_id} has no assigned merchant role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have an assigned merchant role in PayFilter",
        )

    return AuthenticatedUser(
        user_id=user_id,
        merchant_id=str(merchant_id),
        role=str(role),
        email=claims.get("email"),
    )


def require_role(required_role: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Factory returning a dependency that enforces RBAC role privileges."""

    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        check_role_permission(current_user, required_role)
        return current_user

    return role_checker


def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    merchants_repo: MerchantsRepository = Depends(get_merchants_repo),
) -> str:
    """Dependency validating merchant API key on pre-order check routes."""
    return verify_merchant_api_key(x_api_key, merchants_repo=merchants_repo)
