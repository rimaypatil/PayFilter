"""Razorpay Webhook verification and handling route."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.dependencies import get_audit_repo
from backend.app.integrations.razorpay_client import RazorpayClient, get_razorpay_client

logger = logging.getLogger("payfilter.routes.webhooks")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/razorpay",
    status_code=status.HTTP_200_OK,
    summary="Receives and signature-verifies incoming Razorpay payment events",
)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    rzp_client: RazorpayClient = Depends(get_razorpay_client),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> Dict[str, Any]:
    """Processes incoming payment status updates from Razorpay.

    Security Requirement:
    Verifies the HMAC SHA-256 signature against the raw request body BEFORE parsing JSON.
    """
    # 1. Read raw body bytes
    raw_body = await request.body()

    # 2. Strict signature verification
    if not x_razorpay_signature or not rzp_client.verify_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Rejected Razorpay webhook request: Invalid or missing X-Razorpay-Signature.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature. Request rejected.",
        )

    # 3. Parse JSON after signature is cryptographically proven authentic
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse validated webhook JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON body.",
        )

    event = payload.get("event", "unknown_event")
    event_payload = payload.get("payload", {})
    payment_entity = event_payload.get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    notes = payment_entity.get("notes", {})
    merchant_id = notes.get("merchant_id", "a0000000-0000-0000-0000-000000000001")
    payfilter_txn_id = notes.get("payfilter_txn_id")

    logger.info(f"Received authentic Razorpay webhook event: '{event}' for order '{order_id}'")

    # 4. Record to cryptographic audit chain
    audit_entry = audit_repo.append_audit_entry(
        merchant_id=merchant_id,
        action=f"razorpay_webhook:{event}",
        transaction_id=payfilter_txn_id,
        actor="razorpay_webhook",
    )

    return {
        "status": "received",
        "event": event,
        "order_id": order_id,
        "audit_log_id": audit_entry.id or "",
    }
