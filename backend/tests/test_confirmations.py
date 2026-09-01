"""Human confirmation workflow test suite (approve/deny held transactions)."""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.main import app
from backend.app.risk_engine.model import get_model_manager


@pytest.fixture(autouse=True)
def setup_db():
    reset_in_memory_db()
    get_model_manager().initialize()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


def create_token(user_id: str, merchant_id: str, role: str = "analyst") -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "aud": settings.SUPABASE_AUDIENCE,
        "email": f"{user_id}@payfilter.io",
        "merchant_id": merchant_id,
        "role": role,
        "app_metadata": {"merchant_id": merchant_id, "role": role},
        "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def test_analyst_can_approve_held_transaction(client):
    """Analyst confirms a held transaction with 'approve'."""
    repo = MerchantsRepository()
    txns_repo = TransactionsRepository()
    audit_repo = AuditRepository()

    merchant, _ = repo.create_merchant("Merchant A")
    analyst_token = create_token("analyst_alice", merchant.id, role="analyst")

    # Seed a held transaction
    txn_id = "held-txn-0000-0000-000000000001"
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant.id,
        "customer_id": "cust_123",
        "amount": 5000.0,
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.55,
        "reason": {"decision": "held", "primary_driver": "medium_anomaly_score"},
        "model_version": "1.0.0",
    })

    res = client.post(
        f"/transactions/{txn_id}/confirm",
        json={"decision": "approve"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["transaction_id"] == txn_id
    assert data["status"] == "approved"
    assert data["previous_status"] == "held"
    assert data["confirmed_by"] == "analyst_alice"
    assert data["audit_log_id"] != ""

    # Verify DB status updated
    persisted = txns_repo.get_transaction_by_id(txn_id)
    assert persisted.status == "approved"

    # Verify audit log entry
    logs, _ = audit_repo.get_audit_log(merchant_id=merchant.id)
    actions = [l.action for l in logs]
    assert any("confirmed_by_human:approved" in a for a in actions)


def test_analyst_can_deny_held_transaction(client):
    """Analyst confirms a held transaction with 'deny' -> resolves to 'blocked'."""
    repo = MerchantsRepository()
    txns_repo = TransactionsRepository()

    merchant, _ = repo.create_merchant("Merchant A")
    analyst_token = create_token("analyst_bob", merchant.id, role="analyst")

    txn_id = "held-txn-0000-0000-000000000002"
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant.id,
        "customer_id": "cust_123",
        "amount": 15000.0,
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.62,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
    })

    res = client.post(
        f"/transactions/{txn_id}/confirm",
        json={"decision": "deny"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "blocked"

    persisted = txns_repo.get_transaction_by_id(txn_id)
    assert persisted.status == "blocked"


def test_cannot_confirm_non_held_transaction(client):
    """Attempting to confirm an already approved or blocked transaction returns 400."""
    repo = MerchantsRepository()
    txns_repo = TransactionsRepository()

    merchant, _ = repo.create_merchant("Merchant A")
    analyst_token = create_token("analyst_1", merchant.id, role="analyst")

    txn_id = "approved-txn-0000-000000000001"
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant.id,
        "customer_id": "cust_123",
        "amount": 100.0,
        "agent_type": "procurement_agent",
        "status": "approved",
        "risk_score": 0.1,
        "reason": {"decision": "approved"},
        "model_version": "1.0.0",
    })

    res = client.post(
        f"/transactions/{txn_id}/confirm",
        json={"decision": "approve"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 400
    assert "only 'held' transactions can be confirmed" in res.json()["detail"].lower()


def test_cannot_confirm_other_merchants_transaction(client):
    """User from Merchant A cannot confirm Merchant B's held transaction (403)."""
    repo = MerchantsRepository()
    txns_repo = TransactionsRepository()

    merchant_a, _ = repo.create_merchant("Merchant A")
    merchant_b, _ = repo.create_merchant("Merchant B")

    analyst_a_token = create_token("analyst_a", merchant_a.id, role="analyst")

    txn_b_id = "held-txn-merchant-b-0000000001"
    txns_repo.create_transaction({
        "id": txn_b_id,
        "merchant_id": merchant_b.id,
        "customer_id": "cust_999",
        "amount": 2000.0,
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.50,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
    })

    res = client.post(
        f"/transactions/{txn_b_id}/confirm",
        json={"decision": "approve"},
        headers={"Authorization": f"Bearer {analyst_a_token}"},
    )
    assert res.status_code == 403
    assert "another merchant" in res.json()["detail"].lower()
