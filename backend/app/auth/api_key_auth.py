"""Merchant Backend API Key Authentication Module."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.app.db.repository.merchants_repo import MerchantsRepository

logger = logging.getLogger("payfilter.auth.api_key")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_merchant_api_key(
    api_key: Optional[str] = Security(api_key_header),
    merchants_repo: Optional[MerchantsRepository] = None,
) -> str:
    """Validates incoming merchant API key by hashed lookup.

    Args:
        api_key: Value passed in X-API-Key header.
        merchants_repo: Optional repository instance override.

    Returns:
        str: Validated merchant_id UUID.

    Raises:
        HTTPException: 401 Unauthorized if key is missing, invalid, or unrecognized.
    """
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Merchant API Key is required (pass in 'X-API-Key' header)",
        )

    clean_key = api_key.strip()
    repo = merchants_repo or MerchantsRepository()
    merchant = repo.get_merchant_by_api_key(clean_key)

    if not merchant:
        logger.warning("Authentication failed: Unrecognized API key hash")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unrecognized API Key",
        )

    return merchant.id
