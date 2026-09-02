"""Supabase JWT Signature & Claims Verification Module."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError

from backend.app.config import get_settings

logger = logging.getLogger("payfilter.auth.jwt")


def create_mock_jwt(user_id: str, merchant_id: str = "default_merchant", role: str = "analyst", expires_in: int = 3600) -> str:
    """Generates a valid signed JWT for testing."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "aud": settings.SUPABASE_AUDIENCE,
        "email": f"{user_id}@payfilter.io",
        "merchant_id": merchant_id,
        "role": role,
        "app_metadata": {"merchant_id": merchant_id, "role": role},
        "exp": now + timedelta(seconds=expires_in),
        "iat": now,
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """Cryptographically verifies a Supabase JWT against secret/JWKS.

    Validates signature, expiry, and required claims.
    Rejects expired tokens, invalid signatures, or missing claims with HTTP 401.

    Args:
        token: Raw JWT token string (without 'Bearer ' prefix).

    Returns:
        Dict[str, Any]: Verified payload claims.

    Raises:
        HTTPException: 401 Unauthorized if verification fails.
    """
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    jwt_secret = settings.SUPABASE_JWT_SECRET

    try:
        # Decode and verify signature with HS256 / configured secret
        # Supabase defaults to HS256 with project JWT secret
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256", "RS256"],
            audience=settings.SUPABASE_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": bool(settings.SUPABASE_AUDIENCE),
                "require": ["exp", "sub"],
            },
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("Supabase JWT validation failed: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidSignatureError:
        logger.warning("Supabase JWT validation failed: Invalid signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as e:
        logger.warning(f"Supabase JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
