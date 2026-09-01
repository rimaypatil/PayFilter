"""Unit tests for Razorpay test-mode client integration & webhook signature verification."""

import hashlib
import hmac
import pytest
from unittest.mock import MagicMock, patch

from backend.app.config import Settings
from backend.app.integrations.razorpay_client import RazorpayClient


def test_razorpay_create_order_success():
    """Verifies that an approved transaction creates a test order ID."""
    client = RazorpayClient(key_id="rzp_test_123456", key_secret="secret_123456")
    
    txn_data = {
        "id": "11111111-2222-3333-4444-555555555555",
        "merchant_id": "a0000000-0000-0000-0000-000000000001",
        "customer_id": "cust_alice",
        "amount": 1500.50,
        "agent_type": "procurement_agent",
    }
    
    order_id = client.create_order(txn_data)
    assert order_id is not None
    assert order_id.startswith("order_")


def test_razorpay_create_order_failure_tolerance():
    """Verifies that an external Razorpay API error does NOT crash or raise, but returns None."""
    client = RazorpayClient(key_id="rzp_test_123456", key_secret="secret_123456")
    
    # Mock SDK client to raise an exception
    mock_sdk = MagicMock()
    mock_sdk.order.create.side_effect = Exception("Razorpay API 500 Internal Error")
    client._client = mock_sdk
    
    txn_data = {
        "id": "11111111-2222-3333-4444-555555555555",
        "merchant_id": "a0000000-0000-0000-0000-000000000001",
        "customer_id": "cust_alice",
        "amount": 2500.00,
    }
    
    # Should not raise exception
    order_id = client.create_order(txn_data)
    assert order_id is None


def test_razorpay_webhook_signature_valid():
    """Verifies valid HMAC SHA256 signature is accepted."""
    secret = "test_webhook_secret_xyz"
    client = RazorpayClient()
    client.webhook_secret = secret
    
    payload = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_123"}}}}'
    valid_signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    
    assert client.verify_webhook_signature(payload, valid_signature) is True


def test_razorpay_webhook_signature_invalid():
    """Verifies incorrect or tampered signature is rejected."""
    secret = "test_webhook_secret_xyz"
    client = RazorpayClient()
    client.webhook_secret = secret
    
    payload = b'{"event":"payment.captured"}'
    invalid_signature = "bad_signature_hex_digest_12345"
    
    assert client.verify_webhook_signature(payload, invalid_signature) is False


def test_razorpay_webhook_signature_tampered_payload():
    """Verifies signature calculated for payload A fails when payload is tampered to payload B."""
    secret = "test_webhook_secret_xyz"
    client = RazorpayClient()
    client.webhook_secret = secret
    
    payload_original = b'{"amount":1000}'
    payload_tampered = b'{"amount":999999}'
    
    signature = hmac.new(secret.encode("utf-8"), payload_original, hashlib.sha256).hexdigest()
    
    assert client.verify_webhook_signature(payload_tampered, signature) is False


def test_live_key_rejection_security_guard():
    """Verifies config startup check refuses live-mode key without explicit override."""
    with pytest.raises(ValueError, match="SECURITY VIOLATION"):
        settings = Settings(
            RAZORPAY_KEY_ID="rzp_live_abc123456789",
            ALLOW_LIVE_KEYS=False,
        )
        settings.validate_test_keys()
