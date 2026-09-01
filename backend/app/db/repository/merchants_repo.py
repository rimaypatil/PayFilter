"""Repository for merchants table operations."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional
from backend.app.db.client import get_supabase_client
from backend.app.db.models import Merchant


class MerchantsRepository:
    """Provides access to merchant accounts."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client or get_supabase_client()

    def get_merchant_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Fetches merchant record by UUID."""
        res = self.client.table("merchants").select("*").eq("id", merchant_id).single().execute()
        if res.data:
            return Merchant(**res.data)
        return None

    def create_merchant(self, name: str, api_key: str, merchant_id: Optional[str] = None) -> Merchant:
        """Registers a new merchant."""
        api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        data = {
            "name": name,
            "api_key_hash": api_key_hash,
        }
        if merchant_id:
            data["id"] = merchant_id
        res = self.client.table("merchants").insert(data)
        item = res.data[0] if isinstance(res.data, list) else res.data
        return Merchant(**item)
