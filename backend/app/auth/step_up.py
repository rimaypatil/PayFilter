"""Step-Up Authentication & One-Time Code Flow for Critical Actions."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import secrets
from typing import Dict, Optional
from fastapi import HTTPException, status

logger = logging.getLogger("payfilter.auth.step_up")

# Server-side stateful store: (user_id, action) -> { code, expires_at }
_STEP_UP_STORE: Dict[tuple[str, str], Dict[str, Any]] = {}


def generate_step_up_code(
    user_id: str,
    action: str = "kill_switch",
    expiry_seconds: int = 300,
) -> tuple[str, datetime]:
    """Generates a short-lived 6-digit numeric OTP for step-up verification.

    Args:
        user_id: UUID of the authenticated admin requesting step-up.
        action: Target high-risk action identifier.
        expiry_seconds: Expiry window in seconds (default 5 minutes).

    Returns:
        tuple[str, datetime]: (6-digit code, expiry_datetime)
    """
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() + expiry_seconds,
        tz=timezone.utc,
    )

    _STEP_UP_STORE[(user_id, action)] = {
        "code": code,
        "expires_at": expires_at,
    }

    logger.info(f"Step-up code issued for user {user_id} (action={action}, expires in {expiry_seconds}s)")
    return code, expires_at


def validate_and_consume_step_up_code(
    user_id: str,
    code: str,
    action: str = "kill_switch",
) -> bool:
    """Validates and immediately consumes a one-time step-up code.

    Args:
        user_id: UUID of the admin attempting execution.
        code: 6-digit code submitted in request.
        action: Target action.

    Returns:
        bool: True if code is valid and unexpired.

    Raises:
        HTTPException: 403 Forbidden if code is missing, incorrect, or expired.
    """
    key = (user_id, action)
    entry = _STEP_UP_STORE.get(key)

    if not entry:
        logger.warning(f"Step-up validation failed: No active code requested for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up authentication required. Request a verification code first via /kill-switch/request.",
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    if now > entry["expires_at"]:
        _STEP_UP_STORE.pop(key, None)
        logger.warning(f"Step-up validation failed: Code expired for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up verification code has expired. Please request a new code.",
        )

    # Validate code
    if str(entry["code"]) != str(code).strip():
        logger.warning(f"Step-up validation failed: Invalid code for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid step-up verification code.",
        )

    # Consume on success (one-time use)
    _STEP_UP_STORE.pop(key, None)
    logger.info(f"Step-up verification succeeded and consumed for user {user_id}")
    return True


def clear_step_up_store() -> None:
    """Helper for testing to reset step-up state."""
    _STEP_UP_STORE.clear()
