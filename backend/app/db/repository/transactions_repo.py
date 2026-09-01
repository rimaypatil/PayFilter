"""Repository for transactions table operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.db.client import get_supabase_client
from backend.app.db.models import TransactionRecord


class TransactionsRepository:
    """Provides access and persistence for transactions."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client or get_supabase_client()

    def get_transaction_by_id(self, transaction_id: str) -> Optional[TransactionRecord]:
        """Fetches a transaction by UUID for idempotency lookup."""
        try:
            res = (
                self.client.table("transactions")
                .select("*")
                .eq("id", transaction_id)
                .single()
                .execute()
            )
            if res.data:
                return TransactionRecord(**res.data)
        except Exception:
            return None
        return None

    def create_transaction(self, record_data: Dict[str, Any]) -> TransactionRecord:
        """Persists a new scored transaction record."""
        res = self.client.table("transactions").insert(record_data)
        item = res.data[0] if isinstance(res.data, list) else res.data
        return TransactionRecord(**item)

    def get_customer_history(
        self,
        customer_id: str,
        before_timestamp: datetime,
        merchant_id: Optional[str] = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """Fetches confirmed historical transactions strictly prior to before_timestamp.

        Returns:
            pd.DataFrame: Formatted DataFrame suitable for extract_single_transaction_features.
        """
        query = (
            self.client.table("transactions")
            .select("*")
            .eq("customer_id", customer_id)
            .lt("created_at", before_timestamp.isoformat())
            .order("created_at", desc=False)
            .limit(limit)
        )
        if merchant_id:
            query = query.eq("merchant_id", merchant_id)

        res = query.execute()
        rows = res.data if isinstance(res.data, list) else []

        if not rows:
            return pd.DataFrame(
                columns=[
                    "transaction_id",
                    "customer_id",
                    "merchant_id",
                    "amount",
                    "timestamp",
                    "merchant_category",
                    "agent_type",
                ]
            )

        df = pd.DataFrame(rows)
        # Normalize columns for ML feature extractor
        if "id" in df.columns and "transaction_id" not in df.columns:
            df["transaction_id"] = df["id"]
        if "created_at" in df.columns and "timestamp" not in df.columns:
            df["timestamp"] = pd.to_datetime(df["created_at"])
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        if "merchant_category" not in df.columns:
            # Fallback if merchant_category stored in reason or column
            df["merchant_category"] = "general"

        return df

    def get_recent_transactions_count(
        self,
        merchant_id: str,
        since_timestamp: datetime,
    ) -> int:
        """Counts total transactions across merchant within a recent timeframe (for velocity checks)."""
        res = (
            self.client.table("transactions")
            .select("id", count="exact")
            .eq("merchant_id", merchant_id)
            .gte("created_at", since_timestamp.isoformat())
            .execute()
        )
        return res.count if hasattr(res, "count") and res.count is not None else len(res.data or [])
