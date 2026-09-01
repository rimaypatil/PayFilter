"""Step-up authentication and kill switch test suite."""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.app.auth.step_up import clear_step_up_store
from backend.app.config import get_settings
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.main import app
from backend.app.risk_engine.model import get_model_manager


@pytest.fixture(autouse=True)
def setup_db():
    reset_in_memory_db()
    clear_step_up_store()
    get_model_manager().initialize()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


def create_token(user_id: str, merchant_id: str, role: str = "admin") -> str:
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


def test_kill_switch_confirm_without_request_fails(client):
    """Calling /kill-switch/confirm without requesting step-up OTP first returns 403."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")
    admin_token = create_token("admin_user", merchant.id, role="admin")

    res = client.post(
        "/kill-switch/confirm",
        json={"code": "123456", "is_active": True, "reason": "Emergency"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 403
    assert "step-up authentication required" in res.json()["detail"].lower()


def test_kill_switch_confirm_with_wrong_code_fails(client):
    """Calling /kill-switch/confirm with incorrect OTP code returns 403."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")
    admin_token = create_token("admin_user", merchant.id, role="admin")

    # 1. Request valid code
    req_res = client.post(
        "/kill-switch/request",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert req_res.status_code == 200

    # 2. Submit wrong code
    res = client.post(
        "/kill-switch/confirm",
        json={"code": "000000", "is_active": True, "reason": "Emergency"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 403
    assert "invalid step-up" in res.json()["detail"].lower()


def test_kill_switch_end_to_end_activation_blocks_transactions(client):
    """Full step-up kill switch flow: request -> confirm -> verify all incoming txns blocked."""
    repo = MerchantsRepository()
    merchant, api_key = repo.create_merchant("Test Org")
    admin_token = create_token("admin_user", merchant.id, role="admin")

    # 1. Check transaction passes initially
    txn_payload = {
        "transaction_id": "00000000-1111-2222-3333-444444444444",
        "merchant_id": merchant.id,
        "customer_id": "cust_1",
        "amount": 250.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    init_res = client.post(
        "/transactions/check",
        json=txn_payload,
        headers={"X-API-Key": api_key},
    )
    assert init_res.status_code == 200
    assert init_res.json()["status"] == "approved"

    # 2. Admin requests step-up code
    req_res = client.post(
        "/kill-switch/request",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert req_res.status_code == 200
    otp_code = req_res.json()["code"]

    # 3. Admin confirms kill switch activation using code
    confirm_res = client.post(
        "/kill-switch/confirm",
        json={"code": otp_code, "is_active": True, "reason": "Suspected API breach"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["is_active"] is True
    assert "ACTIVE" in confirm_res.json()["status"]

    # 4. Incoming transactions now immediately blocked by risk engine
    new_txn_payload = {
        "transaction_id": "00000000-1111-2222-3333-555555555555",
        "merchant_id": merchant.id,
        "customer_id": "cust_1",
        "amount": 250.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    blocked_res = client.post(
        "/transactions/check",
        json=new_txn_payload,
        headers={"X-API-Key": api_key},
    )
    assert blocked_res.status_code == 200
    assert blocked_res.json()["status"] == "blocked"
    assert blocked_res.json()["reason"]["primary_driver"] == "kill_switch_activated"
