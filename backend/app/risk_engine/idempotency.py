"""Idempotency enforcement to prevent duplicate scoring or duplicate writes."""

from __future__ import annotations

from typing import Optional, Tuple
from backend.app.db.models import TransactionRecord
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.schemas import TransactionCheckResponse


class IdempotencyChecker:
    """Guarantees idempotent transaction evaluation."""

    def __init__(self, transactions_repo: Optional[TransactionsRepository] = None):
        self.transactions_repo = transactions_repo or TransactionsRepository()

    def check_existing(
        self,
        transaction_id: str,
        audit_log_id: Optional[str] = None,
    ) -> Optional[TransactionCheckResponse]:
        """Checks if transaction_id was already scored.

        Args:
            transaction_id: Transaction UUID to query.
            audit_log_id: Optional audit log id if known.

        Returns:
            Optional[TransactionCheckResponse]: Previously stored decision, or None if new.
        """
        existing: Optional[TransactionRecord] = self.transactions_repo.get_transaction_by_id(transaction_id)
        if existing is not None:
            # Build previously saved response
            return TransactionCheckResponse(
                transaction_id=existing.id,
                status=existing.status,  # type: ignore
                risk_score=existing.risk_score,
                reason=existing.reason,
                audit_log_id=audit_log_id or str(existing.id),
            )
        return None
