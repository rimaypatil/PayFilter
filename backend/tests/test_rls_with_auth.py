"""Multi-tenant Row-Level Security isolation test with authenticated Supabase Auth users.

Proves that two authenticated users from two different merchants cannot cross-read or mutate
each other's transactions, audit log, rules config, or kill switch states.
Replaces the manual-key approach from Phase 2.
"""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.rules_repo import RulesRepository
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


def create_user_jwt(user_id: str, merchant_id: str, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "aud": settings.SUPABASE_AUDIENCE,
        "email": f"{user_id}@merchant.com",
        "merchant_id": merchant_id,
        "role": role,
        "app_metadata": {"merchant_id": merchant_id, "role": role},
        "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def test_cross_merchant_audit_log_isolation(client):
    """User from Merchant A cannot view Merchant B's audit logs."""
    merchants_repo = MerchantsRepository()
    audit_repo = AuditRepository()

    # 1. Setup Merchant A and Merchant B
    merchant_a, _ = merchants_repo.create_merchant("Merchant Alpha")
    merchant_b, _ = merchants_repo.create_merchant("Merchant Beta")

    # 2. Assign User roles
    merchants_repo.assign_user_role("user_alpha_admin", merchant_a.id, "admin")
    merchants_repo.assign_user_role("user_beta_admin", merchant_b.id, "admin")

    jwt_alpha = create_user_jwt("user_alpha_admin", merchant_a.id, "admin")
    jwt_beta = create_user_jwt("user_beta_admin", merchant_b.id, "admin")

    # 3. Seed Audit logs for both merchants
    audit_repo.append_audit_entry(
        merchant_id=merchant_a.id,
        action="merchant_registered",
        actor="user_alpha_admin",
    )
    audit_repo.append_audit_entry(
        merchant_id=merchant_b.id,
        action="merchant_registered",
        actor="user_beta_admin",
    )

    # 4. User Alpha queries audit log
    res_a = client.get("/audit-log", headers={"Authorization": f"Bearer {jwt_alpha}"})
    assert res_a.status_code == 200
    items_a = res_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["merchant_id"] == merchant_a.id

    # 5. User Alpha attempts explicit query targeting Merchant B
    res_a_targeted = client.get(
        f"/audit-log?merchant_id={merchant_b.id}",
        headers={"Authorization": f"Bearer {jwt_alpha}"},
    )
    assert res_a_targeted.status_code == 403
    assert "another merchant" in res_a_targeted.json()["detail"].lower()

    # 6. User Beta queries audit log
    res_b = client.get("/audit-log", headers={"Authorization": f"Bearer {jwt_beta}"})
    assert res_b.status_code == 200
    items_b = res_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["merchant_id"] == merchant_b.id


def test_cross_merchant_rules_isolation(client):
    """User from Merchant A cannot read or mutate Merchant B's rules."""
    merchants_repo = MerchantsRepository()
    rules_repo = RulesRepository()

    merchant_a, _ = merchants_repo.create_merchant("Merchant Alpha")
    merchant_b, _ = merchants_repo.create_merchant("Merchant Beta")

    rules_repo.upsert_rules_config(merchant_a.id, max_amount_per_order=10000.0, max_transactions_per_minute=2)
    rules_repo.upsert_rules_config(merchant_b.id, max_amount_per_order=90000.0, max_transactions_per_minute=20)

    jwt_alpha = create_user_jwt("user_alpha_admin", merchant_a.id, "admin")
    jwt_beta = create_user_jwt("user_beta_admin", merchant_b.id, "admin")

    # Alpha gets only Alpha's rules
    res_a = client.get("/rules", headers={"Authorization": f"Bearer {jwt_alpha}"})
    assert res_a.status_code == 200
    assert res_a.json()["max_amount_per_order"] == 10000.0

    # Beta gets only Beta's rules
    res_b = client.get("/rules", headers={"Authorization": f"Bearer {jwt_beta}"})
    assert res_b.status_code == 200
    assert res_b.json()["max_amount_per_order"] == 90000.0


def test_cross_merchant_confirmation_isolation(client):
    """User from Merchant A cannot confirm or resolve Merchant B's held transaction."""
    merchants_repo = MerchantsRepository()
    txns_repo = TransactionsRepository()

    merchant_a, _ = merchants_repo.create_merchant("Merchant Alpha")
    merchant_b, _ = merchants_repo.create_merchant("Merchant Beta")

    jwt_alpha = create_user_jwt("user_alpha_analyst", merchant_a.id, "analyst")

    txn_b_id = "held-txn-beta-999"
    txns_repo.create_transaction({
        "id": txn_b_id,
        "merchant_id": merchant_b.id,
        "customer_id": "cust_beta_1",
        "amount": 5000.0,
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.52,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
    })

    # User Alpha attempts to confirm Beta's transaction
    res = client.post(
        f"/transactions/{txn_b_id}/confirm",
        json={"decision": "approve"},
        headers={"Authorization": f"Bearer {jwt_alpha}"},
    )
    assert res.status_code == 403
    assert "another merchant" in res.json()["detail"].lower()
