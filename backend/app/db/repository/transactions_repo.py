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

    def update_transaction_status(
        self,
        transaction_id: str,
        status: str,
        reason: Optional[Any] = None,
        razorpay_order_id: Optional[str] = None,
    ) -> Optional[TransactionRecord]:
        """Updates the status, reason, and optional razorpay_order_id of an existing transaction."""
        update_payload: Dict[str, Any] = {"status": status}
        if reason is not None:
            update_payload["reason"] = reason
        if razorpay_order_id is not None:
            update_payload["razorpay_order_id"] = razorpay_order_id

        res = self.client.table("transactions").update(update_payload).eq("id", transaction_id).execute()
        if res.data and len(res.data) > 0:
            return TransactionRecord(**res.data[0])
        # In mock or postgres return refreshed record
        return self.get_transaction_by_id(transaction_id)

    def get_unresolved_held_transactions(
        self,
        older_than_timestamp: datetime,
        merchant_id: Optional[str] = None,
    ) -> List[TransactionRecord]:
        """Queries for transactions currently in 'held' status created before older_than_timestamp."""
        query = (
            self.client.table("transactions")
            .select("*")
            .eq("status", "held")
            .lte("created_at", older_than_timestamp.isoformat())
        )
        if merchant_id:
            query = query.eq("merchant_id", merchant_id)

        res = query.execute()
        rows = res.data if isinstance(res.data, list) else []
        return [TransactionRecord(**r) for r in rows]

    def get_transactions(
        self,
        merchant_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[TransactionRecord], int]:
        """Fetches paginated transactions for a merchant with optional status filtering."""
        query = (
            self.client.table("transactions")
            .select("*")
            .eq("merchant_id", merchant_id)
        )
        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).offset(offset).limit(limit)
        res = query.execute()
        rows = res.data if isinstance(res.data, list) else []
        total = res.count if hasattr(res, "count") and res.count is not None else len(rows)
        return [TransactionRecord(**r) for r in rows], total
