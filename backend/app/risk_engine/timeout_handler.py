"""Background Timeout Handler for Held Transactions.

Auto-resolves unreviewed held transactions past a configurable expiration window:
- Large transactions (> LARGE_AMOUNT_THRESHOLD) default safely to 'blocked'.
- Smaller/normal transactions (<= LARGE_AMOUNT_THRESHOLD) default to 'approved'.
- Writes cryptographic audit log entry with action='auto_resolved_timeout'.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional
from backend.app.config import get_settings
from backend.app.db.models import TransactionRecord
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository

logger = logging.getLogger("payfilter.risk_engine.timeout_handler")


class TimeoutHandler:
    """Manages scheduled timeout auto-resolution of stale held transactions."""

    def __init__(
        self,
        transactions_repo: Optional[TransactionsRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.txns_repo = transactions_repo or TransactionsRepository()
        self.audit_repo = audit_repo or AuditRepository()
        self.settings = get_settings()

    def process_held_timeouts(
        self,
        timeout_seconds: Optional[int] = None,
        large_threshold: Optional[float] = None,
        merchant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Scans for and resolves all held transactions older than timeout threshold.

        Args:
            timeout_seconds: Custom timeout duration in seconds (overrides settings).
            large_threshold: Amount threshold for safe blocked resolution (overrides settings).
            merchant_id: Optional merchant UUID filter.

        Returns:
            List[Dict[str, Any]]: Summary of all auto-resolved transactions.
        """
        sec = timeout_seconds if timeout_seconds is not None else self.settings.HELD_TIMEOUT_SECONDS
        large_amt = large_threshold if large_threshold is not None else self.settings.LARGE_AMOUNT_THRESHOLD

        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=sec)
        stale_held_txns = self.txns_repo.get_unresolved_held_transactions(
            older_than_timestamp=cutoff_time,
            merchant_id=merchant_id,
        )

        resolved_records = []

        for txn in stale_held_txns:
            # Safe default policy:
            # High amount -> blocked
            # Standard amount -> approved
            if txn.amount > large_amt:
                resolved_status = "blocked"
                reason_detail = f"Auto-resolved to blocked on timeout ({txn.amount} exceeds safe hold threshold of {large_amt})"
            else:
                resolved_status = "approved"
                reason_detail = f"Auto-resolved to approved on timeout ({txn.amount} within low-risk threshold)"

            reason_payload = {
                **(txn.reason or {}),
                "resolution": "auto_resolved_timeout",
                "resolved_status": resolved_status,
                "timeout_seconds": sec,
                "detail": reason_detail,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }

            # 1. Update status in database
            updated_txn = self.txns_repo.update_transaction_status(
                transaction_id=txn.id,
                status=resolved_status,
                reason=reason_payload,
            )

            # 2. Append to immutable cryptographic audit log
            audit_entry = self.audit_repo.append_audit_entry(
                merchant_id=txn.merchant_id,
                action=f"auto_resolved_timeout:{resolved_status}",
                transaction_id=txn.id,
                actor="system_timeout",
            )

            logger.info(
                f"Held transaction '{txn.id}' auto-resolved to '{resolved_status}' "
                f"(amount={txn.amount}, audit_id={audit_entry.id})"
            )

            resolved_records.append({
                "transaction_id": txn.id,
                "merchant_id": txn.merchant_id,
                "amount": txn.amount,
                "resolved_status": resolved_status,
                "audit_log_id": audit_entry.id,
                "reason": reason_detail,
            })

        return resolved_records


_timeout_handler_instance: Optional[TimeoutHandler] = None


def get_timeout_handler() -> TimeoutHandler:
    """Returns singleton TimeoutHandler instance."""
    global _timeout_handler_instance
    if _timeout_handler_instance is None:
        _timeout_handler_instance = TimeoutHandler()
    return _timeout_handler_instance
