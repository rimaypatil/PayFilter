"""Audit log query route (GET /audit-log) with JWT Authentication & Tenant Scoping."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.db.models import AuthenticatedUser
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.dependencies import get_current_user, require_role
from backend.app.schemas import AuditLogEntry, AuditLogResponse

router = APIRouter(prefix="/audit-log", tags=["Audit"])


def get_audit_repo() -> AuditRepository:
    return AuditRepository()


@router.get(
    "",
    response_model=AuditLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve paginated cryptographic audit trail (Requires Analyst/Admin Auth)",
)
def get_audit_trail(
    merchant_id: Optional[str] = Query(None, description="Optional merchant UUID filter (must match caller)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(require_role("analyst")),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> AuditLogResponse:
    """Returns paginated, immutable audit trail records scoped strictly to calling merchant.

    # FRONTEND: audit trail page calls this in Phase 4
    """
    # Enforce tenant isolation
    target_merchant_id = current_user.merchant_id
    if merchant_id and merchant_id != target_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access audit logs belonging to another merchant.",
        )

    offset = (page - 1) * page_size
    records, total = audit_repo.get_audit_log(
        merchant_id=target_merchant_id,
        limit=page_size,
        offset=offset,
    )

    items = [
        AuditLogEntry(
            id=r.id or "",
            transaction_id=r.transaction_id,
            merchant_id=r.merchant_id,
            action=r.action,
            actor=r.actor,
            prev_hash=r.prev_hash,
            row_hash=r.row_hash,
            created_at=r.created_at or "",
        )
        for r in records
    ]

    return AuditLogResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
