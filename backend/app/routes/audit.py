"""Audit log query route (GET /audit-log)."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.schemas import AuditLogEntry, AuditLogResponse

router = APIRouter(prefix="/audit-log", tags=["Audit"])


def get_audit_repo() -> AuditRepository:
    return AuditRepository()


@router.get(
    "",
    response_model=AuditLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve paginated cryptographic audit trail",
)
def get_audit_trail(
    merchant_id: Optional[str] = Query(None, description="Filter by merchant UUID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> AuditLogResponse:
    """Returns paginated, immutable audit trail records.

    # AUTH: added in Phase 3 (merchant_id scoping will be enforced via JWT session claims)
    """
    offset = (page - 1) * page_size
    records, total = audit_repo.get_audit_log(
        merchant_id=merchant_id,
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
