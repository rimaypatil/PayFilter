"""Repository for transactions table operations."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.db.client import get_supabase_client
from backend.app.db.models import TransactionRecord


logger = logging.getLogger("payfilter.db.transactions")


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
        except Exception as e:
            logger.debug(f"[DB] get_transaction_by_id lookup error for id={transaction_id}: {e}")

        return None

    def create_transaction(self, record_data: Dict[str, Any]) -> TransactionRecord:
        """Persists a new scored transaction record."""
        merchant_id = str(record_data.get("merchant_id", ""))
        logger.info("[DB] inserting transaction")
        logger.info("[DB] transaction repository table=transactions")
        logger.info(f"[DB] merchant_id={merchant_id}")

        if hasattr(self.client, "db_store"):
            res = self.client.table("transactions").insert(record_data)
            item = res.data[0] if isinstance(res.data, list) else res.data
            logger.info("[DB] database response status=201 (in-memory)")
            return TransactionRecord(**item)

        try:
            res = self.client.table("transactions").insert(record_data).execute()
            status_code = getattr(res, "status_code", 201) if hasattr(res, "status_code") else 201
            logger.info(f"[DB] database response status={status_code}")
            item = res.data[0] if (res.data and isinstance(res.data, list)) else res.data
            if item:
                return TransactionRecord(**item)
        except Exception as e:
            logger.error(f"[DB] database insert error: {e}")
            # Direct REST fallback using service key
            try:
                from backend.app.config import get_settings
                import httpx
                settings = get_settings()
                if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY and "mock" not in settings.SUPABASE_URL:
                    headers = {
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    }
                    resp = httpx.post(
                        f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/transactions",
                        headers=headers,
                        json=record_data,
                        timeout=5.0,
                    )
                    logger.info(f"[DB] database response status={resp.status_code}")
                    if resp.status_code in [200, 201]:
                        rows = resp.json()
                        item = rows[0] if isinstance(rows, list) else rows
                        return TransactionRecord(**item)
                    else:
                        logger.error(f"[DB] Direct REST insert failed: status={resp.status_code}, body={resp.text}")
            except Exception as direct_err:
                logger.error(f"[DB] Direct REST insert exception: {direct_err}")
            raise e

        raise RuntimeError("Failed to persist transaction to Supabase database.")

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
        logger.info("[DB] transaction repository table=transactions")
        logger.info(f"[DB] merchant_id={merchant_id}")

        if hasattr(self.client, "db_store"):
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
            logger.info("[DB] database response status=200 (in-memory)")
            return [TransactionRecord(**r) for r in rows], total

        try:
            query = (
                self.client.table("transactions")
                .select("*", count="exact")
                .eq("merchant_id", merchant_id)
            )
            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True).offset(offset).limit(limit)
            res = query.execute()
            status_code = getattr(res, "status_code", 200) if hasattr(res, "status_code") else 200
            logger.info(f"[DB] database response status={status_code}")
            rows = res.data if isinstance(res.data, list) else []
            total = res.count if hasattr(res, "count") and res.count is not None else len(rows)
            return [TransactionRecord(**r) for r in rows], total
        except Exception as e:
            logger.error(f"[DB] database query error: {e}")
            # Direct REST fallback with service key
            try:
                from backend.app.config import get_settings
                import httpx
                settings = get_settings()
                if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY and "mock" not in settings.SUPABASE_URL:
                    headers = {
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                        "Range-Unit": "items",
                        "Prefer": "count=exact",
                    }
                    params = {
                        "select": "*",
                        "merchant_id": f"eq.{merchant_id}",
                        "order": "created_at.desc",
                        "offset": str(offset),
                        "limit": str(limit),
                    }
                    if status:
                        params["status"] = f"eq.{status}"
                    resp = httpx.get(
                        f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/transactions",
                        headers=headers,
                        params=params,
                        timeout=5.0,
                    )
                    logger.info(f"[DB] database response status={resp.status_code}")
                    if resp.status_code in [200, 206]:
                        rows = resp.json()
                        total = len(rows)
                        content_range = resp.headers.get("content-range", "")
                        if "/" in content_range:
                            try:
                                total = int(content_range.split("/")[-1])
                            except Exception:
                                pass
                        return [TransactionRecord(**r) for r in rows], total
                    else:
                        logger.error(f"[DB] Direct REST query failed: status={resp.status_code}, body={resp.text}")
            except Exception as direct_err:
                logger.error(f"[DB] Direct REST query exception: {direct_err}")
            raise e
