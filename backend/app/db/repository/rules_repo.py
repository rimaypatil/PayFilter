"""Repository for rules_config table operations."""

from __future__ import annotations

from typing import Any, Dict, Optional
from backend.app.db.client import get_supabase_client
from backend.app.db.models import RulesConfig


class RulesRepository:
    """Provides access to merchant-configured rules limits."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client or get_supabase_client()

    def get_rules_config(self, merchant_id: str) -> RulesConfig:
        """Fetches rules config for merchant, or returns default baseline if not configured."""
        try:
            res = (
                self.client.table("rules_config")
                .select("*")
                .eq("merchant_id", merchant_id)
                .single()
                .execute()
            )
            if res.data:
                return RulesConfig(**res.data)
        except Exception:
            pass

        # Return default fallback rules config if none exists in DB
        return RulesConfig(merchant_id=merchant_id)

    def upsert_rules_config(
        self,
        merchant_id: str,
        max_amount_per_order: float,
        max_transactions_per_minute: int,
        category_limits: Optional[Dict[str, float]] = None,
    ) -> RulesConfig:
        """Upserts rules configuration for a merchant."""
        payload = {
            "merchant_id": merchant_id,
            "max_amount_per_order": max_amount_per_order,
            "max_transactions_per_minute": max_transactions_per_minute,
            "category_limits": category_limits or {},
        }
        res = self.client.table("rules_config").insert(payload)
        item = res.data[0] if isinstance(res.data, list) else res.data
        return RulesConfig(**item)
