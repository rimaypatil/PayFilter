"""Tests for secure Merchant API Key Management, Rotation, and RBAC."""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.main import app
from backend.app.risk_engine.model import get_model_manager


@pytest.fixture(autouse=True)
def setup_db():
    reset_in_memory_db()
    get_model_manager().initialize()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


def create_token(user_id: str, merchant_id: str, role: str) -> str:
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


def test_get_api_key_status_admin(client):
    """Admin can view masked API key overview and endpoint."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Acme Corp")
    admin_token = create_token("admin_1", merchant.id, role="admin")

    res = client.get(
        "/merchants/api-key/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["merchant_id"] == merchant.id
    assert data["is_active"] is True
    assert data["masked_key"] == "pf_live_••••••••••••••••"
    assert "transaction_endpoint" in data
    assert "api_key" not in data  # Never exposes plaintext on status check


def test_get_api_key_status_analyst(client):
    """Analyst can also view masked API key overview."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Beta Retail")
    analyst_token = create_token("analyst_1", merchant.id, role="analyst")

    res = client.get(
        "/merchants/api-key/status",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["merchant_id"] == merchant.id
    assert data["is_active"] is True
    assert data["masked_key"] == "pf_live_••••••••••••••••"


def test_analyst_cannot_rotate_api_key(client):
    """Analyst calling POST /merchants/api-key/rotate receives 403 Forbidden."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Secure Merchant")
    analyst_token = create_token("analyst_1", merchant.id, role="analyst")

    res = client.post(
        "/merchants/api-key/rotate",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 403
    assert "admin" in res.json()["detail"].lower()


def test_admin_rotate_api_key_lifecycle(client):
    """Full lifecycle: Admin rotates key, receives new key once, old key stops working, new key works."""
    repo = MerchantsRepository()
    merchant, initial_key = repo.create_merchant("Omni Store")
    admin_token = create_token("admin_1", merchant.id, role="admin")

    # 1. Verify initial key works on /transactions/check
    txn_payload = {
        "transaction_id": "txn_test_001",
        "amount": 500.0,
        "customer_id": "cust_123",
        "agent_type": "autonomous_buyer",
    }
    check_res1 = client.post(
        "/transactions/check",
        json=txn_payload,
        headers={"X-API-Key": initial_key},
    )
    assert check_res1.status_code == 200
    assert check_res1.json()["status"].lower() in ["approved", "held", "blocked"]

    # 2. Admin rotates key
    rotate_res = client.post(
        "/merchants/api-key/rotate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rotate_res.status_code == 200
    new_key = rotate_res.json()["api_key"]
    assert new_key != initial_key
    assert new_key.startswith("pf_live_")

    # 3. Old key immediately stops working (401 Unauthorized)
    check_res_old = client.post(
        "/transactions/check",
        json={"transaction_id": "txn_test_002", "amount": 500.0, "customer_id": "cust_123"},
        headers={"X-API-Key": initial_key},
    )
    assert check_res_old.status_code == 401

    # 4. New key works on /transactions/check
    check_res_new = client.post(
        "/transactions/check",
        json={"transaction_id": "txn_test_003", "amount": 500.0, "customer_id": "cust_123"},
        headers={"X-API-Key": new_key},
    )
    assert check_res_new.status_code == 200
    assert check_res_new.json()["status"].lower() in ["approved", "held", "blocked"]


def test_unauthenticated_cannot_access_or_rotate(client):
    """Requests without token fail with 401."""
    res_status = client.get("/merchants/api-key/status")
    assert res_status.status_code == 401

    res_rotate = client.post("/merchants/api-key/rotate")
    assert res_rotate.status_code == 401
