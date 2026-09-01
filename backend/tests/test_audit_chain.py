"""Unit and security tests for cryptographic audit chain and tamper detection."""

import pytest

from backend.app.db.audit_chain import GENESIS_HASH, hash_row, verify_chain, verify_chain_entries
from backend.app.db.client import InMemorySupabaseClient
from backend.app.db.repository.audit_repo import AuditRepository


def test_genesis_hash_first_entry():
    """Verify first audit entry uses GENESIS_HASH and correctly links."""
    client = InMemorySupabaseClient()
    repo = AuditRepository(client=client)

    entry1 = repo.append_audit_entry(
        merchant_id="merchant_alpha",
        action="transaction_scored:approved",
        transaction_id="txn_001",
        actor="system",
        created_at="2026-08-30T10:00:00Z",
    )

    assert entry1.prev_hash == GENESIS_HASH
    assert entry1.row_hash != GENESIS_HASH
    assert len(entry1.row_hash) == 64


def test_audit_chain_sequential_integrity():
    """Verify multiple sequential entries form a valid cryptographic chain."""
    client = InMemorySupabaseClient()
    repo = AuditRepository(client=client)
    merchant_id = "merchant_beta"

    e1 = repo.append_audit_entry(merchant_id=merchant_id, action="action_1", transaction_id="t1", created_at="2026-08-30T10:00:00Z")
    e2 = repo.append_audit_entry(merchant_id=merchant_id, action="action_2", transaction_id="t2", created_at="2026-08-30T10:01:00Z")
    e3 = repo.append_audit_entry(merchant_id=merchant_id, action="action_3", transaction_id="t3", created_at="2026-08-30T10:02:00Z")

    assert e2.prev_hash == e1.row_hash
    assert e3.prev_hash == e2.row_hash

    # Clean chain must verify as True
    assert verify_chain(merchant_id=merchant_id, client=client) is True


def test_deliberate_tamper_detection_in_audit_chain():
    """Security test: Deliberately modifying an audit record's contents breaks the hash chain."""
    client = InMemorySupabaseClient()
    repo = AuditRepository(client=client)
    merchant_id = "merchant_gamma"

    repo.append_audit_entry(merchant_id=merchant_id, action="action_1", transaction_id="t1", created_at="2026-08-30T10:00:00Z")
    repo.append_audit_entry(merchant_id=merchant_id, action="action_2", transaction_id="t2", created_at="2026-08-30T10:01:00Z")
    repo.append_audit_entry(merchant_id=merchant_id, action="action_3", transaction_id="t3", created_at="2026-08-30T10:02:00Z")

    # Clean chain verifies
    assert verify_chain(merchant_id=merchant_id, client=client) is True

    # Tamper with the 2nd record directly in storage (e.g. malicious actor changing action)
    audit_rows = client.db_store["audit_log"]
    target_row = [r for r in audit_rows if r["transaction_id"] == "t2"][0]
    target_row["action"] = "action_2_TAMPERED"

    # Verification must now return False!
    assert verify_chain(merchant_id=merchant_id, client=client) is False


def test_deliberate_prev_hash_tamper_detection():
    """Security test: Tampering with prev_hash link causes verify_chain to return False."""
    client = InMemorySupabaseClient()
    repo = AuditRepository(client=client)
    merchant_id = "merchant_delta"

    repo.append_audit_entry(merchant_id=merchant_id, action="action_1", transaction_id="t1", created_at="2026-08-30T10:00:00Z")
    repo.append_audit_entry(merchant_id=merchant_id, action="action_2", transaction_id="t2", created_at="2026-08-30T10:01:00Z")

    # Corrupt prev_hash of second row
    audit_rows = client.db_store["audit_log"]
    audit_rows[1]["prev_hash"] = "0" * 64

    assert verify_chain(merchant_id=merchant_id, client=client) is False
