"""Authentication tests for PayFilter (Supabase JWT & Merchant API Keys)."""

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


def create_token(
    user_id: str,
    merchant_id: str,
    role: str = "analyst",
    secret: str = None,
    expired: bool = False,
) -> str:
    settings = get_settings()
    jwt_secret = secret or settings.SUPABASE_JWT_SECRET
    exp = (
        datetime.now(timezone.utc) - timedelta(seconds=300)
        if expired
        else datetime.now(timezone.utc) + timedelta(seconds=3600)
    )
    payload = {
        "sub": user_id,
        "aud": settings.SUPABASE_AUDIENCE,
        "email": f"{user_id}@payfilter.io",
        "merchant_id": merchant_id,
        "role": role,
        "app_metadata": {"merchant_id": merchant_id, "role": role},
        "exp": exp,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def test_missing_jwt_token_returns_401(client):
    """Protected human route with missing Authorization header returns 401."""
    res = client.get("/audit-log")
    assert res.status_code == 401
    assert "token is required" in res.json()["detail"].lower() or "missing" in res.json()["detail"].lower()


def test_expired_jwt_token_returns_401(client):
    """Expired JWT token returns 401 Unauthorized."""
    expired_token = create_token("user_1", "m_1", role="analyst", expired=True)
    res = client.get("/audit-log", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_tampered_jwt_signature_returns_401(client):
    """Token signed with wrong key or tampered signature returns 401."""
    invalid_sig_token = create_token("user_1", "m_1", role="analyst", secret="wrong-secret-key-123456789")
    res = client.get("/audit-log", headers={"Authorization": f"Bearer {invalid_sig_token}"})
    assert res.status_code == 401
    assert "signature" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()


def test_missing_merchant_api_key_returns_401(client):
    """Calling POST /transactions/check without X-API-Key returns 401."""
    payload = {
        "transaction_id": "00000000-0000-0000-0000-000000000001",
        "merchant_id": "a0000000-0000-0000-0000-000000000001",
        "customer_id": "cust_1",
        "amount": 100.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    res = client.post("/transactions/check", json=payload)
    assert res.status_code == 401
    assert "api key" in res.json()["detail"].lower()


def test_invalid_merchant_api_key_returns_401(client):
    """Calling POST /transactions/check with unmapped API key returns 401."""
    payload = {
        "transaction_id": "00000000-0000-0000-0000-000000000001",
        "merchant_id": "a0000000-0000-0000-0000-000000000001",
        "customer_id": "cust_1",
        "amount": 100.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    res = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": "pf_live_invalid_fake_key_12345"},
    )
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower() or "unrecognized" in res.json()["detail"].lower()


def test_valid_api_key_succeeds(client):
    """Calling POST /transactions/check with valid registered API key succeeds (200)."""
    repo = MerchantsRepository()
    merchant, api_key = repo.create_merchant(name="Acme Corp")

    payload = {
        "transaction_id": "00000000-0000-0000-0000-000000000002",
        "merchant_id": merchant.id,
        "customer_id": "cust_1",
        "amount": 150.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    res = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    assert res.status_code == 200
    assert res.json()["transaction_id"] == payload["transaction_id"]
    assert res.json()["status"] in ["approved", "held", "blocked"]
