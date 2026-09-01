"""Razorpay Test-Mode Orders API and Webhook Verification Integration."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional
import uuid

from backend.app.config import get_settings

logger = logging.getLogger("payfilter.integrations.razorpay")


class RazorpayClient:
    """Wrapper around Razorpay Orders API and Webhook verification in test mode."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        settings = get_settings()
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        self._client = None
        if self.key_id and self.key_secret:
            try:
                import razorpay
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
                logger.info(f"Initialized Razorpay client with key: {self.key_id[:8]}...")
            except Exception as e:
                logger.warning(f"Could not initialize official Razorpay SDK client: {e}. Using resilient test fallback.")

    def create_order(self, transaction: Dict[str, Any]) -> Optional[str]:
        """Creates a test-mode order on Razorpay for an approved transaction.

        Failure-Tolerant Principle:
        If Razorpay API errors or is unreachable, this method returns None and logs the failure.
        The PayFilter approval decision remains valid and recorded.

        Args:
            transaction: Dictionary containing transaction details (id, amount, merchant_id, customer_id).

        Returns:
            Optional[str]: Created razorpay_order_id (e.g. 'order_test_...') or None if creation failed.
        """
        transaction_id = str(transaction.get("id") or transaction.get("transaction_id") or "")
        amount = float(transaction.get("amount", 0.0))
        amount_paise = int(round(amount * 100))

        order_payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": transaction_id,
            "notes": {
                "payfilter_txn_id": transaction_id,
                "merchant_id": str(transaction.get("merchant_id", "")),
                "customer_id": str(transaction.get("customer_id", "")),
                "agent_type": str(transaction.get("agent_type", "autonomous")),
            },
        }

        # 1. If official SDK client available with live test keys, invoke API
        if self._client:
            try:
                order_response = self._client.order.create(data=order_payload)
                order_id = order_response.get("id")
                logger.info(f"Successfully created Razorpay test order '{order_id}' for transaction {transaction_id}")
                return order_id
            except Exception as exc:
                logger.error(
                    f"Razorpay Orders API call failed for transaction {transaction_id}: {exc}. "
                    "Preserving PayFilter approval decision.",
                    exc_info=True,
                )
                return None

        # 2. Resilient Test-Mode Simulator (for local testing / automated CI)
        mock_order_id = f"order_test_{uuid.uuid4().hex[:14]}"
        logger.info(f"[Test-Mode Simulator] Generated Razorpay test order '{mock_order_id}' for transaction {transaction_id}")
        return mock_order_id

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verifies incoming Razorpay webhook signature using constant-time HMAC SHA256 comparison.

        Security Requirement:
        Verification must happen on raw request bytes BEFORE any JSON parsing.

        Args:
            payload: Raw bytes of the HTTP request body.
            signature: X-Razorpay-Signature HTTP header value.

        Returns:
            bool: True if signature matches authentic HMAC digest, False otherwise.
        """
        if not signature or not self.webhook_secret:
            logger.warning("Webhook signature verification failed: Missing signature header or webhook secret.")
            return False

        try:
            expected_digest = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected_digest, signature)
        except Exception as e:
            logger.error(f"Error computing webhook HMAC signature: {e}")
            return False


_global_razorpay_client: Optional[RazorpayClient] = None


def get_razorpay_client() -> RazorpayClient:
    """Dependency / factory for Razorpay client."""
    global _global_razorpay_client
    if _global_razorpay_client is None:
        _global_razorpay_client = RazorpayClient()
    return _global_razorpay_client
