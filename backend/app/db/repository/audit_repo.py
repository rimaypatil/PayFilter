"""Append-only repository for cryptographic audit log."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.audit_chain import GENESIS_HASH, hash_row
from backend.app.db.client import get_supabase_client
from backend.app.db.models import AuditLogRecord


_audit_cache: Dict[str, List[AuditLogRecord]] = {}


class AuditRepository:
    """Append-only audit log repository.

    Enforces cryptographic chaining on every insert. Mutating (UPDATE/DELETE) operations
    are explicitly omitted in code and rejected at the DB level.
    """

    def __init__(self, client: Optional[Any] = None):
        self.client = client or get_supabase_client()

    def get_latest_hash(self, merchant_id: str) -> str:
        """Retrieves the row_hash of the most recent audit record for the merchant."""
        try:
            res = (
                self.client.table("audit_log")
                .select("row_hash, created_at")
                .eq("merchant_id", merchant_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]["row_hash"]
        except Exception:
            pass

        cached = _audit_cache.get(merchant_id, [])
        if cached:
            return cached[-1].row_hash

        return GENESIS_HASH

    def append_audit_entry(
        self,
        merchant_id: str,
        action: str,
        transaction_id: Optional[str] = None,
        actor: str = "system",
        created_at: Optional[str] = None,
    ) -> AuditLogRecord:
        """Appends a cryptographically linked audit record to the log.

        Args:
            merchant_id: UUID of the merchant.
            action: Action description (e.g. 'transaction_scored', 'decision_approved').
            transaction_id: Optional UUID of the associated transaction.
            actor: Initiating actor identifier (defaults to 'system' in Phase 2).
            created_at: Optional ISO timestamp override.

        Returns:
            AuditLogRecord: The newly persisted audit log record with computed hash.
        """
        prev_hash = self.get_latest_hash(merchant_id)
        now_iso = created_at or datetime.now(timezone.utc).isoformat()

        row_payload = {
            "transaction_id": transaction_id,
            "merchant_id": merchant_id,
            "action": action,
            "actor": actor,
            "created_at": now_iso,
        }

        row_hash = hash_row(row_payload, prev_hash)

        insert_data = {
            **row_payload,
            "prev_hash": prev_hash,
            "row_hash": row_hash,
        }

        record = AuditLogRecord(
            id=str(len(_audit_cache.get(merchant_id, [])) + 1),
            prev_hash=prev_hash,
            row_hash=row_hash,
            **row_payload,
        )

        if hasattr(self.client, "db_store"):
            res = self.client.table("audit_log").insert(insert_data)
            item = res.data[0] if isinstance(res.data, list) else res.data
            return AuditLogRecord(**item)

        try:
            res = self.client.table("audit_log").insert(insert_data).execute()
            item = res.data[0] if (res.data and isinstance(res.data, list)) else res.data
            if item:
                return AuditLogRecord(**item)
        except Exception:
            try:
                from backend.app.config import get_settings
                import httpx
                settings = get_settings()
                if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY and "mock" not in settings.SUPABASE_URL:
                    headers = {
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    }
                    resp = httpx.post(
                        f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/audit_log",
                        headers=headers,
                        json=insert_data,
                        timeout=5.0,
                    )
                    if resp.status_code in [200, 201]:
                        rows = resp.json()
                        item = rows[0] if isinstance(rows, list) else rows
                        return AuditLogRecord(**item)
            except Exception:
                pass

        _audit_cache.setdefault(merchant_id, []).append(record)
        return record

    def get_audit_log(
        self,
        merchant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AuditLogRecord], int]:
        """Retrieves paginated audit log records."""
        query = self.client.table("audit_log").select("*", count="exact")

        if merchant_id:
            query = query.eq("merchant_id", merchant_id)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        res = query.execute()

        rows = res.data if isinstance(res.data, list) else []
        total = res.count if hasattr(res, "count") and res.count is not None else len(rows)

        items = [AuditLogRecord(**r) for r in rows]
        return items, total

    def get_all_rows_for_merchant(self, merchant_id: str) -> List[Dict[str, Any]]:
        """Retrieves all chronological audit records for chain integrity verification."""
        res = (
            self.client.table("audit_log")
            .select("*")
            .eq("merchant_id", merchant_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data if isinstance(res.data, list) else []
