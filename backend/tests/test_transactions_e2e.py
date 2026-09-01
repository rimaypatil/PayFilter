"""End-to-end integration tests for Razorpay orders & Claude explanations."""

import hashlib
import hmac
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.db.client import get_supabase_client
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def setup_e2e_merchant():
    """Sets up a test merchant with API key and returns merchant_id, plaintext_api_key."""
    db_client = get_supabase_client()
    merchants_repo = MerchantsRepository(db_client)

    merchant_id = f"e2e-merchant-{uuid.uuid4().hex[:8]}"
    raw_api_key, _ = merchants_repo.create_merchant(merchant_id=merchant_id, name="E2E Test Merchant")
    return merchant_id, raw_api_key


def test_e2e_approved_transaction_creates_razorpay_order(setup_e2e_merchant):
    """Verifies that an approved transaction receives a real/simulated Razorpay order ID."""
    merchant_id, api_key = setup_e2e_merchant
    txn_id = str(uuid.uuid4())

    payload = {
        "transaction_id": txn_id,
        "merchant_id": merchant_id,
        "customer_id": "cust_normal_shopper",
        "amount": 450.00,  # Low, normal purchase amount
        "timestamp": "2026-09-01T12:00:00Z",
        "merchant_category": "groceries",
        "agent_type": "grocery_bot",
    }

    response = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["razorpay_order_id"] is not None
    assert str(data["razorpay_order_id"]).startswith("order_")


def test_e2e_blocked_transaction_generates_claude_explanation(setup_e2e_merchant):
    """Verifies that a blocked transaction attaches a plain-English explanation."""
    merchant_id, api_key = setup_e2e_merchant
    txn_id = str(uuid.uuid4())

    payload = {
        "transaction_id": txn_id,
        "merchant_id": merchant_id,
        "customer_id": "cust_fraud_risk",
        "amount": 999999.00,  # Massive spike violating max order cap
        "timestamp": "2026-09-01T12:00:00Z",
        "merchant_category": "luxury_crypto",
        "agent_type": "autonomous_loop",
    }

    response = client.post(
        "/transactions/check",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked"
    assert data["razorpay_order_id"] is None
    
    # Assert plain-English explanation generated
    reason = data["reason"]
    assert "explanation" in reason
    explanation = reason["explanation"]
    assert isinstance(explanation, str)
    assert len(explanation) > 15


def test_e2e_webhook_valid_signature_creates_audit_entry(setup_e2e_merchant):
    """Verifies that authentic Razorpay webhook is accepted and logged."""
    merchant_id, _ = setup_e2e_merchant
    settings = get_settings()
    secret = settings.RAZORPAY_WEBHOOK_SECRET or "mock_razorpay_webhook_secret_12345"

    body_bytes = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_test_999","order_id":"order_test_123","notes":{"merchant_id":"' + merchant_id.encode() + b'","payfilter_txn_id":"txn_test_456"}}}}}'
    signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    response = client.post(
        "/webhooks/razorpay",
        content=body_bytes,
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["event"] == "payment.captured"
    assert data["audit_log_id"] is not None


def test_e2e_webhook_invalid_signature_rejected():
    """Verifies that an unauthorized/tampered webhook is rejected before processing."""
    body_bytes = b'{"event":"payment.captured"}'
    invalid_signature = "bad_forged_signature_12345"

    response = client.post(
        "/webhooks/razorpay",
        content=body_bytes,
        headers={"X-Razorpay-Signature": invalid_signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert "Invalid webhook signature" in response.json()["detail"]
