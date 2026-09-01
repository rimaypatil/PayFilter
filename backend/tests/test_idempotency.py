"""Unit tests for idempotency guarantee."""

from datetime import datetime, timezone
import pytest

from backend.app.db.client import InMemorySupabaseClient
from backend.app.db.models import TransactionRecord
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.risk_engine.idempotency import IdempotencyChecker


def test_idempotency_new_transaction():
    """Verify new transaction ID returns None from checker."""
    client = InMemorySupabaseClient()
    repo = TransactionsRepository(client=client)
    checker = IdempotencyChecker(transactions_repo=repo)

    result = checker.check_existing("new-txn-1234")
    assert result is None


def test_idempotency_duplicate_transaction():
    """Verify repeated transaction ID returns cached decision without re-scoring."""
    client = InMemorySupabaseClient()
    repo = TransactionsRepository(client=client)

    txn_id = "duplicate-txn-5678"
    saved_record = {
        "id": txn_id,
        "merchant_id": "m1",
        "customer_id": "cust_100",
        "amount": 450.00,
        "agent_type": "procurement_agent",
        "status": "approved",
        "risk_score": 0.1234,
        "reason": {"decision": "approved", "primary_driver": "normal_baseline"},
        "model_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    repo.create_transaction(saved_record)

    checker = IdempotencyChecker(transactions_repo=repo)
    cached_response = checker.check_existing(txn_id)

    assert cached_response is not None
    assert cached_response.transaction_id == txn_id
    assert cached_response.status == "approved"
    assert cached_response.risk_score == 0.1234
    assert cached_response.reason["decision"] == "approved"
