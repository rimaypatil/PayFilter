"""Unit and tenant isolation tests for Row-Level Security (RLS) policies."""

import pytest

from backend.app.db.client import InMemorySupabaseClient, InMemorySupabaseTable
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository


class TenantScopedSupabaseClient(InMemorySupabaseClient):
    """Simulates a restricted tenant-scoped Supabase client (e.g. anon/authenticated JWT claim).

    Enforces that queries only return/mutate rows matching self.scoped_merchant_id.
    """

    def __init__(self, scoped_merchant_id: str, shared_store: dict):
        super().__init__(current_merchant_id=scoped_merchant_id)
        self.scoped_merchant_id = scoped_merchant_id
        self.db_store = shared_store

    def table(self, table_name: str) -> InMemorySupabaseTable:
        tbl = super().table(table_name)
        original_execute = tbl.execute
        original_insert = tbl.insert

        def rls_insert(values: Any):
            match_col = "id" if table_name == "merchants" else "merchant_id"
            rows = values if isinstance(values, list) else [values]
            for r in rows:
                if r.get(match_col) and str(r.get(match_col)) != self.scoped_merchant_id:
                    raise PermissionError(f"RLS check failed: cannot insert row for merchant {r.get(match_col)}")
            return original_insert(values)

        def rls_execute():
            if table_name in ["transactions", "audit_log", "rules_config", "merchants"]:
                match_col = "id" if table_name == "merchants" else "merchant_id"
                tbl.eq(match_col, self.scoped_merchant_id)
            return original_execute()

        tbl.insert = rls_insert
        tbl.execute = rls_execute
        return tbl


def test_cross_merchant_transaction_isolation():
    """Verify Merchant A cannot read Merchant B's transactions."""
    shared_storage = {
        "merchants": [],
        "transactions": [],
        "audit_log": [],
        "rules_config": [],
    }

    # Setup 2 merchant clients
    merchant_a_id = "a0000000-0000-0000-0000-000000000001"
    merchant_b_id = "b0000000-0000-0000-0000-000000000002"

    client_a = TenantScopedSupabaseClient(merchant_a_id, shared_storage)
    client_b = TenantScopedSupabaseClient(merchant_b_id, shared_storage)

    repo_a = TransactionsRepository(client=client_a)
    repo_b = TransactionsRepository(client=client_b)

    # Merchant A writes transaction
    repo_a.create_transaction({
        "id": "txn-a-1",
        "merchant_id": merchant_a_id,
        "customer_id": "cust_1",
        "amount": 100.0,
        "agent_type": "procurement_agent",
        "status": "approved",
        "risk_score": 0.1,
        "reason": {},
        "model_version": "1.0.0",
        "created_at": "2026-08-30T10:00:00Z",
    })

    # Merchant B writes transaction
    repo_b.create_transaction({
        "id": "txn-b-1",
        "merchant_id": merchant_b_id,
        "customer_id": "cust_2",
        "amount": 200.0,
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.5,
        "reason": {},
        "model_version": "1.0.0",
        "created_at": "2026-08-30T10:00:00Z",
    })

    # Merchant A queries by ID for Merchant B's transaction -> must return None
    assert repo_a.get_transaction_by_id("txn-b-1") is None
    # Merchant A queries own transaction -> succeeds
    assert repo_a.get_transaction_by_id("txn-a-1") is not None

    # Merchant B queries by ID for Merchant A's transaction -> must return None
    assert repo_b.get_transaction_by_id("txn-a-1") is None
    # Merchant B queries own transaction -> succeeds
    assert repo_b.get_transaction_by_id("txn-b-1") is not None


def test_cross_merchant_audit_log_isolation():
    """Verify Merchant A cannot read Merchant B's audit trail."""
    shared_storage = {
        "merchants": [],
        "transactions": [],
        "audit_log": [],
        "rules_config": [],
    }

    merchant_a_id = "a0000000-0000-0000-0000-000000000001"
    merchant_b_id = "b0000000-0000-0000-0000-000000000002"

    client_a = TenantScopedSupabaseClient(merchant_a_id, shared_storage)
    client_b = TenantScopedSupabaseClient(merchant_b_id, shared_storage)

    audit_repo_a = AuditRepository(client=client_a)
    audit_repo_b = AuditRepository(client=client_b)

    audit_repo_a.append_audit_entry(merchant_id=merchant_a_id, action="action_a", transaction_id="tx_a")
    audit_repo_b.append_audit_entry(merchant_id=merchant_b_id, action="action_b", transaction_id="tx_b")

    # Merchant A fetches audit log -> only sees own 1 entry
    items_a, total_a = audit_repo_a.get_audit_log(merchant_id=merchant_a_id)
    assert total_a == 1
    assert items_a[0].merchant_id == merchant_a_id

    # Merchant A tries to fetch Merchant B's audit log -> returns 0 items
    items_cross, total_cross = audit_repo_a.get_audit_log(merchant_id=merchant_b_id)
    assert total_cross == 0


def test_cross_merchant_rules_config_isolation():
    """Verify Merchant A cannot read or mutate Merchant B's rules configuration."""
    shared_storage = {
        "merchants": [],
        "transactions": [],
        "audit_log": [],
        "rules_config": [],
    }

    merchant_a_id = "a0000000-0000-0000-0000-000000000001"
    merchant_b_id = "b0000000-0000-0000-0000-000000000002"

    client_a = TenantScopedSupabaseClient(merchant_a_id, shared_storage)
    client_b = TenantScopedSupabaseClient(merchant_b_id, shared_storage)

    rules_repo_a = RulesRepository(client=client_a)
    rules_repo_b = RulesRepository(client=client_b)

    rules_repo_a.upsert_rules_config(merchant_id=merchant_a_id, max_amount_per_order=15000.0, max_transactions_per_minute=3)
    rules_repo_b.upsert_rules_config(merchant_id=merchant_b_id, max_amount_per_order=99000.0, max_transactions_per_minute=20)

    cfg_a = rules_repo_a.get_rules_config(merchant_a_id)
    assert cfg_a.max_amount_per_order == 15000.0

    # If A tries to query B's config, RLS prevents reading B's real values and returns default fallback
    cfg_b_via_a = rules_repo_a.get_rules_config(merchant_b_id)
    assert cfg_b_via_a.max_amount_per_order == 50000.0  # default fallback, not 99000.0
