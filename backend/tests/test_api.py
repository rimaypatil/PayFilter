"""End-to-end API integration tests using FastAPI TestClient with Auth."""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    """Resets in-memory storage before each test."""
    reset_in_memory_db()


@pytest.fixture
def client():
    """Returns FastAPI test client."""
    from backend.app.risk_engine.model import get_model_manager
    get_model_manager().initialize()
    return TestClient(app, raise_server_exceptions=True)


def create_merchant_auth():
    """Creates a test merchant, API key, and authenticated user JWT."""
    repo = MerchantsRepository()
    merchant, api_key = repo.create_merchant(
        name="API Test Merchant",
        merchant_id="a0000000-0000-0000-0000-000000000001",
    )
    repo.assign_user_role("test_admin_user", merchant.id, "admin")

    settings = get_settings()
    payload = {
        "sub": "test_admin_user",
        "aud": settings.SUPABASE_AUDIENCE,
        "email": "admin@apitest.com",
        "merchant_id": merchant.id,
        "role": "admin",
        "app_metadata": {"merchant_id": merchant.id, "role": "admin"},
        "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"merchant_id": merchant.id, "api_key": api_key, "jwt": token}


@pytest.fixture
def merchant_auth():
    """Fixture returning merchant auth context."""
    return create_merchant_auth()


def test_health_endpoint(client):
    """Verify /health returns status ok and valid model version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_version" in data
    assert data["model_loaded"] is True


def test_post_transaction_check_valid_approved(client, merchant_auth):
    """Verify valid low-risk transaction with valid API key returns 200."""
    payload = {
        "transaction_id": "11111111-1111-1111-1111-111111111111",
        "merchant_id": merchant_auth["merchant_id"],
        "customer_id": "cust_demo_1",
        "amount": 150.00,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }

    response = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": merchant_auth["api_key"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == payload["transaction_id"]
    assert data["status"] in ["approved", "held", "blocked"]
    assert "risk_score" in data
    assert "reason" in data
    assert "audit_log_id" in data
    assert len(data["audit_log_id"]) > 0


def test_post_transaction_check_rejected_on_negative_amount(client, merchant_auth):
    """Verify negative amount returns 422 Unprocessable Entity (not 500)."""
    payload = {
        "transaction_id": "22222222-2222-2222-2222-222222222222",
        "merchant_id": merchant_auth["merchant_id"],
        "customer_id": "cust_demo_2",
        "amount": -50.00,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }

    response = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": merchant_auth["api_key"]},
    )
    assert response.status_code == 422


def test_post_transaction_check_rejected_on_extra_fields(client, merchant_auth):
    """Verify unexpected fields return 422 (forbid extra)."""
    payload = {
        "transaction_id": "33333333-3333-3333-3333-333333333333",
        "merchant_id": merchant_auth["merchant_id"],
        "customer_id": "cust_demo_3",
        "amount": 100.00,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
        "unauthorized_extra_field": "exploit_attempt",
    }

    response = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": merchant_auth["api_key"]},
    )
    assert response.status_code == 422


def test_idempotent_duplicate_request(client, merchant_auth):
    """Verify submitting same transaction_id twice returns identical decision."""
    txn_id = "44444444-4444-4444-4444-444444444444"
    payload = {
        "transaction_id": txn_id,
        "merchant_id": merchant_auth["merchant_id"],
        "customer_id": "cust_demo_4",
        "amount": 80.00,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "ecommerce",
        "agent_type": "personal_assistant",
    }

    headers = {"X-API-Key": merchant_auth["api_key"]}

    # 1st request
    res1 = client.post("/transactions/check", json=payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()

    # 2nd duplicate request
    res2 = client.post("/transactions/check", json=payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1["transaction_id"] == data2["transaction_id"]
    assert data1["status"] == data2["status"]
    assert data1["risk_score"] == data2["risk_score"]


def test_audit_log_endpoint_paginated(client, merchant_auth):
    """Verify /audit-log with JWT returns paginated entries for merchant."""
    merchant_id = merchant_auth["merchant_id"]
    api_key = merchant_auth["api_key"]
    jwt_token = merchant_auth["jwt"]

    # Create 2 transactions to populate audit trail
    for i in range(2):
        client.post(
            "/transactions/check",
            json={
                "transaction_id": f"55555555-5555-5555-5555-55555555555{i}",
                "merchant_id": merchant_id,
                "customer_id": "cust_demo_5",
                "amount": 50.00 + i,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "merchant_category": "saas",
                "agent_type": "automated_scheduler",
            },
            headers={"X-API-Key": api_key},
        )

    # Query audit log with JWT authorization
    res = client.get(
        "/audit-log?page=1&page_size=10",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 2
    assert len(body["items"]) >= 2
    assert body["items"][0]["merchant_id"] == merchant_id
