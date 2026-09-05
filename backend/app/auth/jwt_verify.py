"""Supabase JWT Signature & Claims Verification Module."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
import jwt
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError

from backend.app.config import get_settings

logger = logging.getLogger("payfilter.auth.jwt")

_jwks_client: Optional[PyJWKClient] = None
_jwks_url_cached: Optional[str] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Initializes and returns cached PyJWKClient for remote Supabase JWKS."""
    global _jwks_client, _jwks_url_cached
    settings = get_settings()
    supabase_url = settings.SUPABASE_URL
    if not supabase_url or "mock" in supabase_url or "your-project" in supabase_url:
        return None

    jwks_url = settings.SUPABASE_JWKS_URL or f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    if _jwks_client is None or _jwks_url_cached != jwks_url:
        try:
            _jwks_client = PyJWKClient(jwks_url, cache_keys=True, max_cached_keys=16)
            _jwks_url_cached = jwks_url
        except Exception as e:
            logger.warning(f"Could not initialize PyJWKClient for {jwks_url}: {e}")
            return None
    return _jwks_client


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

    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as e:
        logger.warning(f"Supabase JWT header parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    alg = unverified_header.get("alg", "HS256")
    kid = unverified_header.get("kid")

    # 1. Asymmetric or JWKS-based verification (ES256, RS256, or token with kid)
    if alg in ["ES256", "RS256"] or kid:
        jwks_client = get_jwks_client()
        if jwks_client:
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["HS256", "RS256", "ES256"],
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
                logger.warning(f"Supabase JWKS validation failed: {e}")
                if alg != "HS256":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Invalid authentication credentials: {str(e)}",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

    # 2. Symmetric HS256 verification (used for tests or mock secret)
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256", "RS256", "ES256"],
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
    except (InvalidSignatureError, PyJWTError) as e:
        # 3. If local signature check failed and a real Supabase instance is configured,
        # verify the token authoritatively via Supabase Auth API
        supabase_url = settings.SUPABASE_URL
        if supabase_url and "mock" not in supabase_url and "your-project" not in supabase_url:
            try:
                import httpx
                verify_url = f"{supabase_url.rstrip('/')}/auth/v1/user"
                headers = {
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}",
                }
                resp = httpx.get(verify_url, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    user_data = resp.json()
                    user_id = user_data.get("id")
                    if user_id:
                        return {
                            "sub": user_id,
                            "id": user_id,
                            "email": user_data.get("email"),
                            "role": user_data.get("role", "authenticated"),
                            "app_metadata": user_data.get("app_metadata", {}),
                            "user_metadata": user_data.get("user_metadata", {}),
                            "aud": user_data.get("aud", settings.SUPABASE_AUDIENCE),
                        }
                elif resp.status_code == 401:
                    logger.warning("Supabase Auth API rejected token as expired or invalid")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired or is invalid",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            except HTTPException:
                raise
            except Exception as net_err:
                logger.warning(f"Failed to verify token with Supabase Auth API: {net_err}")

        logger.warning(f"Supabase JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
