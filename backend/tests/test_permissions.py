"""Role-based authorization and permissions test suite (Admin vs Analyst)."""

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


def test_analyst_forbidden_from_updating_rules(client):
    """Analyst calling PUT /rules receives 403 Forbidden."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")

    analyst_token = create_token("analyst_1", merchant.id, role="analyst")
    res = client.put(
        "/rules",
        json={"max_amount_per_order": 20000.0},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 403
    assert "admin" in res.json()["detail"].lower()


def test_admin_can_update_rules(client):
    """Admin calling PUT /rules succeeds (200)."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")

    admin_token = create_token("admin_1", merchant.id, role="admin")
    res = client.put(
        "/rules",
        json={"max_amount_per_order": 25000.0, "max_transactions_per_minute": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["max_amount_per_order"] == 25000.0
    assert res.json()["max_transactions_per_minute"] == 10


def test_analyst_forbidden_from_rotating_api_key(client):
    """Analyst calling POST /merchants/api-key/rotate receives 403 Forbidden."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")

    analyst_token = create_token("analyst_1", merchant.id, role="analyst")
    res = client.post(
        "/merchants/api-key/rotate",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 403
    assert "admin" in res.json()["detail"].lower()


def test_admin_can_rotate_api_key(client):
    """Admin calling POST /merchants/api-key/rotate succeeds (200)."""
    repo = MerchantsRepository()
    merchant, old_key = repo.create_merchant("Test Org")

    admin_token = create_token("admin_1", merchant.id, role="admin")
    res = client.post(
        "/merchants/api-key/rotate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert "api_key" in res.json()
    assert res.json()["api_key"] != old_key
    assert res.json()["api_key"].startswith("pf_live_")


def test_analyst_forbidden_from_requesting_kill_switch_otp(client):
    """Analyst calling POST /kill-switch/request receives 403 Forbidden."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")

    analyst_token = create_token("analyst_1", merchant.id, role="analyst")
    res = client.post(
        "/kill-switch/request",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 403
    assert "admin" in res.json()["detail"].lower()


def test_analyst_can_read_rules_and_audit_log(client):
    """Analyst has read privileges on rules and audit log."""
    repo = MerchantsRepository()
    merchant, _ = repo.create_merchant("Test Org")

    analyst_token = create_token("analyst_1", merchant.id, role="analyst")

    rules_res = client.get("/rules", headers={"Authorization": f"Bearer {analyst_token}"})
    assert rules_res.status_code == 200

    audit_res = client.get("/audit-log", headers={"Authorization": f"Bearer {analyst_token}"})
    assert audit_res.status_code == 200
