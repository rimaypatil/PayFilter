"""Repository for merchants, user_roles, API keys, and kill switch operations."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import secrets
from typing import Any, Dict, Optional
from backend.app.db.client import get_supabase_client
from backend.app.db.models import KillSwitchState, Merchant, UserRole


def hash_api_key(plaintext_key: str) -> str:
    """Computes SHA-256 digest of an API key."""
    return hashlib.sha256(plaintext_key.strip().encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    """Generates a cryptographically secure random merchant API key."""
    random_part = secrets.token_urlsafe(32)
    return f"pf_live_{random_part}"


class MerchantsRepository:
    """Provides access to merchant accounts, keys, user roles, and kill switches."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client or get_supabase_client()

    def get_merchant_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Fetches merchant record by UUID."""
        res = self.client.table("merchants").select("*").eq("id", merchant_id).single().execute()
        if res.data:
            return Merchant(**res.data)
        return None

    def get_merchant_by_api_key(self, api_key: str) -> Optional[Merchant]:
        """Looks up a merchant by matching SHA-256 hash of API key."""
        if not api_key:
            return None
        key_hash = hash_api_key(api_key)
        res = self.client.table("merchants").select("*").eq("api_key_hash", key_hash).single().execute()
        if res.data:
            return Merchant(**res.data)
        return None

    def create_merchant(
        self,
        name: str,
        api_key: Optional[str] = None,
        merchant_id: Optional[str] = None,
    ) -> tuple[Merchant, str]:
        """Registers a new merchant with a securely generated and hashed API key.

        Returns:
            tuple[Merchant, str]: (merchant_model, plaintext_api_key)
        """
        plaintext_key = api_key or generate_api_key()
        api_key_hash = hash_api_key(plaintext_key)
        data = {
            "name": name,
            "api_key_hash": api_key_hash,
        }
        if merchant_id:
            data["id"] = merchant_id
        res = self.client.table("merchants").insert(data)
        item = res.data[0] if isinstance(res.data, list) else res.data
        return Merchant(**item), plaintext_key

    def rotate_api_key(self, merchant_id: str) -> str:
        """Rotates merchant API key, invalidates old hash, and returns new plaintext key."""
        new_plaintext_key = generate_api_key()
        new_hash = hash_api_key(new_plaintext_key)

        self.client.table("merchants").update({"api_key_hash": new_hash}).eq("id", merchant_id).execute()
        return new_plaintext_key

    def assign_user_role(self, user_id: str, merchant_id: str, role: str) -> UserRole:
        """Assigns or updates role for a user (admin or analyst)."""
        data = {
            "user_id": user_id,
            "merchant_id": merchant_id,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        res = self.client.table("user_roles").insert(data)
        item = res.data[0] if isinstance(res.data, list) else res.data
        return UserRole(**item)

    def get_user_role(self, user_id: str) -> Optional[UserRole]:
        """Retrieves assigned user role by Supabase Auth user_id."""
        res = self.client.table("user_roles").select("*").eq("user_id", user_id).single().execute()
        if res.data:
            return UserRole(**res.data)
        return None

    def get_kill_switch_state(self, merchant_id: str) -> KillSwitchState:
        """Retrieves current kill switch status for a merchant."""
        res = self.client.table("kill_switch").select("*").eq("merchant_id", merchant_id).single().execute()
        if res.data:
            return KillSwitchState(**res.data)
        return KillSwitchState(merchant_id=merchant_id, is_active=False)

    def set_kill_switch_state(
        self,
        merchant_id: str,
        is_active: bool,
        activated_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> KillSwitchState:
        """Activates or deactivates merchant kill switch."""
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "merchant_id": merchant_id,
            "is_active": is_active,
            "activated_at": now_iso if is_active else None,
            "activated_by": activated_by,
            "reason": reason,
        }
        # In mock or postgres, upsert/insert
        res = self.client.table("kill_switch").insert(payload)
        item = res.data[0] if isinstance(res.data, list) else res.data
        return KillSwitchState(**item)
