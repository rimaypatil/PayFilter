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

    def update_rules_config(
        self,
        merchant_id: str,
        max_amount_per_order: Optional[float] = None,
        max_transactions_per_minute: Optional[int] = None,
        category_limits: Optional[Dict[str, float]] = None,
    ) -> RulesConfig:
        """Updates specific fields of merchant rules configuration."""
        current = self.get_rules_config(merchant_id)
        new_max_amt = max_amount_per_order if max_amount_per_order is not None else current.max_amount_per_order
        new_velocity = max_transactions_per_minute if max_transactions_per_minute is not None else current.max_transactions_per_minute
        new_cats = category_limits if category_limits is not None else current.category_limits

        return self.upsert_rules_config(
            merchant_id=merchant_id,
            max_amount_per_order=new_max_amt,
            max_transactions_per_minute=new_velocity,
            category_limits=new_cats,
        )
