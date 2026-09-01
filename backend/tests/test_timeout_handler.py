"""Background timeout handler test suite (safe auto-resolution of held transactions)."""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.risk_engine.timeout_handler import TimeoutHandler


@pytest.fixture(autouse=True)
def setup_db():
    reset_in_memory_db()


def test_timeout_auto_resolves_large_amount_to_blocked():
    """Held transaction exceeding large threshold defaults safely to 'blocked' on timeout."""
    txns_repo = TransactionsRepository()
    audit_repo = AuditRepository()
    merchants_repo = MerchantsRepository()

    merchant, _ = merchants_repo.create_merchant("Test Org")

    # Stale held transaction created 5 minutes ago (300s > 120s timeout)
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=300)
    txn_id = "stale-large-txn-000000000001"
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant.id,
        "customer_id": "cust_123",
        "amount": 75000.0,  # > 25,000 threshold
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.58,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
        "created_at": stale_time.isoformat(),
    })

    handler = TimeoutHandler(transactions_repo=txns_repo, audit_repo=audit_repo)
    resolved = handler.process_held_timeouts(timeout_seconds=120, large_threshold=25000.0)

    assert len(resolved) == 1
    assert resolved[0]["transaction_id"] == txn_id
    assert resolved[0]["resolved_status"] == "blocked"

    # Verify updated in DB
    updated = txns_repo.get_transaction_by_id(txn_id)
    assert updated.status == "blocked"

    # Verify audit entry
    logs, _ = audit_repo.get_audit_log(merchant_id=merchant.id)
    assert any(l.action == "auto_resolved_timeout:blocked" for l in logs)
    assert any(l.actor == "system_timeout" for l in logs)


def test_timeout_auto_resolves_small_amount_to_approved():
    """Held transaction below threshold defaults safely to 'approved' on timeout."""
    txns_repo = TransactionsRepository()
    audit_repo = AuditRepository()
    merchants_repo = MerchantsRepository()

    merchant, _ = merchants_repo.create_merchant("Test Org")

    stale_time = datetime.now(timezone.utc) - timedelta(seconds=200)
    txn_id = "stale-small-txn-000000000002"
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant.id,
        "customer_id": "cust_123",
        "amount": 1500.0,  # <= 25,000 threshold
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.48,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
        "created_at": stale_time.isoformat(),
    })

    handler = TimeoutHandler(transactions_repo=txns_repo, audit_repo=audit_repo)
    resolved = handler.process_held_timeouts(timeout_seconds=120, large_threshold=25000.0)

    assert len(resolved) == 1
    assert resolved[0]["resolved_status"] == "approved"

    updated = txns_repo.get_transaction_by_id(txn_id)
    assert updated.status == "approved"


def test_fresh_held_transaction_is_not_timed_out():
    """Held transaction younger than timeout remains untouched in 'held' status."""
    txns_repo = TransactionsRepository()
    merchants_repo = MerchantsRepository()

    merchant, _ = merchants_repo.create_merchant("Test Org")

    # Created only 30s ago (timeout is 120s)
    fresh_time = datetime.now(timezone.utc) - timedelta(seconds=30)
    txn_id = "fresh-held-txn-000000000003"
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant.id,
        "customer_id": "cust_123",
        "amount": 5000.0,
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.50,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
        "created_at": fresh_time.isoformat(),
    })

    handler = TimeoutHandler(transactions_repo=txns_repo)
    resolved = handler.process_held_timeouts(timeout_seconds=120)

    assert len(resolved) == 0
    unchanged = txns_repo.get_transaction_by_id(txn_id)
    assert unchanged.status == "held"
