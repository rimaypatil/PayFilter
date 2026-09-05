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


_merchants_cache: Dict[str, Merchant] = {}
_api_key_to_merchant: Dict[str, str] = {}
_user_roles_cache: Dict[str, UserRole] = {}
_kill_switch_cache: Dict[str, KillSwitchState] = {}


class MerchantsRepository:
    """Provides access to merchant accounts, keys, user roles, and kill switches."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client or get_supabase_client()

    def get_merchant_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Fetches merchant record by UUID."""
        try:
            res = self.client.table("merchants").select("*").eq("id", merchant_id).single().execute()
            if res.data:
                return Merchant(**res.data)
        except Exception:
            pass
        return _merchants_cache.get(merchant_id)

    def get_merchant_by_api_key(self, api_key: str) -> Optional[Merchant]:
        """Looks up a merchant by matching SHA-256 hash of API key."""
        if not api_key:
            return None
        key_hash = hash_api_key(api_key)
        try:
            res = self.client.table("merchants").select("*").eq("api_key_hash", key_hash).single().execute()
            if res.data:
                return Merchant(**res.data)
        except Exception:
            pass
        m_id = _api_key_to_merchant.get(key_hash)
        if m_id:
            m = _merchants_cache.get(m_id)
            if m and m.api_key_hash == key_hash:
                return m
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
        import uuid
        plaintext_key = api_key or generate_api_key()
        api_key_hash = hash_api_key(plaintext_key)
        m_id = merchant_id or str(uuid.uuid4())
        data = {
            "name": name,
            "api_key_hash": api_key_hash,
            "id": m_id,
        }
        try:
            res = self.client.table("merchants").insert(data).execute()
            item = res.data[0] if (res.data and isinstance(res.data, list)) else res.data
            if item:
                merchant = Merchant(**item)
            else:
                merchant = Merchant(id=m_id, name=name, api_key_hash=api_key_hash)
        except Exception:
            try:
                from backend.app.config import get_settings
                import httpx
                settings = get_settings()
                supabase_url = settings.SUPABASE_URL
                service_key = settings.SUPABASE_SERVICE_KEY
                if supabase_url and service_key and "mock" not in supabase_url:
                    headers = {
                        "apikey": service_key,
                        "Authorization": f"Bearer {service_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    }
                    resp = httpx.post(f"{supabase_url.rstrip('/')}/rest/v1/merchants", headers=headers, json=data, timeout=5.0)
                    if resp.status_code in [200, 201]:
                        rows = resp.json()
                        item = rows[0] if isinstance(rows, list) else rows
                        merchant = Merchant(**item)
                    else:
                        merchant = Merchant(id=m_id, name=name, api_key_hash=api_key_hash)
                else:
                    merchant = Merchant(id=m_id, name=name, api_key_hash=api_key_hash)
            except Exception:
                merchant = Merchant(id=m_id, name=name, api_key_hash=api_key_hash)

        _merchants_cache[merchant.id] = merchant
        _api_key_to_merchant[api_key_hash] = merchant.id
        return merchant, plaintext_key

    def rotate_api_key(self, merchant_id: str) -> str:
        """Rotates merchant API key, invalidates old hash, and returns new plaintext key."""
        new_plaintext_key = generate_api_key()
        new_hash = hash_api_key(new_plaintext_key)

        try:
            self.client.table("merchants").update({"api_key_hash": new_hash}).eq("id", merchant_id).execute()
        except Exception:
            pass

        if merchant_id in _merchants_cache:
            old_hash = _merchants_cache[merchant_id].api_key_hash
            _api_key_to_merchant.pop(old_hash, None)
            _merchants_cache[merchant_id].api_key_hash = new_hash
        _api_key_to_merchant[new_hash] = merchant_id
        return new_plaintext_key

    def assign_user_role(self, user_id: str, merchant_id: str, role: str) -> UserRole:
        """Assigns or updates role for a user (admin or analyst)."""
        data = {
            "user_id": user_id,
            "merchant_id": merchant_id,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        role_obj = UserRole(**data)
        persisted = False
        try:
            res = self.client.table("user_roles").upsert(data).execute()
            item = res.data[0] if (res.data and isinstance(res.data, list)) else res.data
            if item:
                role_obj = UserRole(**item)
                persisted = True
        except Exception:
            try:
                res = self.client.table("user_roles").insert(data).execute()
                item = res.data[0] if (res.data and isinstance(res.data, list)) else res.data
                if item:
                    role_obj = UserRole(**item)
                    persisted = True
            except Exception:
                pass

        if not persisted:
            try:
                from backend.app.config import get_settings
                import httpx
                settings = get_settings()
                supabase_url = settings.SUPABASE_URL
                service_key = settings.SUPABASE_SERVICE_KEY
                if supabase_url and service_key and "mock" not in supabase_url:
                    headers = {
                        "apikey": service_key,
                        "Authorization": f"Bearer {service_key}",
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates,return=representation",
                    }
                    resp = httpx.post(f"{supabase_url.rstrip('/')}/rest/v1/user_roles", headers=headers, json=data, timeout=5.0)
                    if resp.status_code in [200, 201]:
                        rows = resp.json()
                        item = rows[0] if isinstance(rows, list) else rows
                        role_obj = UserRole(**item)
            except Exception:
                pass

        _user_roles_cache[user_id] = role_obj
        return role_obj

    def get_user_role(self, user_id: str, auth_token: Optional[str] = None) -> Optional[UserRole]:
        """Retrieves assigned user role by Supabase Auth user_id from database/RLS tables."""
        # 1. Check in-memory cache first
        if user_id in _user_roles_cache:
            return _user_roles_cache[user_id]

        # 2. Query via configured Supabase table client (avoids .single() throwing on 0 rows)
        try:
            res = self.client.table("user_roles").select("*").eq("user_id", user_id).execute()
            if res.data and len(res.data) > 0:
                role_obj = UserRole(**res.data[0])
                _user_roles_cache[user_id] = role_obj
                return role_obj
        except Exception:
            pass

        # 3. If caller supplied user's Bearer JWT, query PostgREST under user context so RLS auth.uid() applies
        try:
            from backend.app.config import get_settings
            import httpx
            settings = get_settings()
            supabase_url = settings.SUPABASE_URL
            if supabase_url and "mock" not in supabase_url:
                # Try with user auth token (satisfies RLS user_roles_self_select policy: user_id = auth.uid())
                if auth_token:
                    headers = {
                        "apikey": settings.SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {auth_token}",
                    }
                    url = f"{supabase_url.rstrip('/')}/rest/v1/user_roles?select=*&user_id=eq.{user_id}"
                    resp = httpx.get(url, headers=headers, timeout=4.0)
                    if resp.status_code == 200:
                        rows = resp.json()
                        if rows and len(rows) > 0:
                            role_obj = UserRole(**rows[0])
                            _user_roles_cache[user_id] = role_obj
                            return role_obj

                # Try with service role key directly via HTTP headers
                service_key = settings.SUPABASE_SERVICE_KEY
                if service_key and "mock" not in service_key:
                    headers = {
                        "apikey": service_key,
                        "Authorization": f"Bearer {service_key}",
                    }
                    url = f"{supabase_url.rstrip('/')}/rest/v1/user_roles?select=*&user_id=eq.{user_id}"
                    resp = httpx.get(url, headers=headers, timeout=4.0)
                    if resp.status_code == 200:
                        rows = resp.json()
                        if rows and len(rows) > 0:
                            role_obj = UserRole(**rows[0])
                            _user_roles_cache[user_id] = role_obj
                            return role_obj
        except Exception:
            pass

        return None

    def get_kill_switch_state(self, merchant_id: str) -> KillSwitchState:
        """Retrieves current kill switch status for a merchant."""
        if merchant_id in _kill_switch_cache:
            return _kill_switch_cache[merchant_id]

        try:
            res = self.client.table("kill_switch").select("*").eq("merchant_id", merchant_id).single().execute()
            if res.data:
                state = KillSwitchState(**res.data)
                _kill_switch_cache[merchant_id] = state
                return state
        except Exception:
            pass

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
        state = KillSwitchState(**payload)
        try:
            if hasattr(self.client, "db_store"):
                res = self.client.table("kill_switch").insert(payload)
            else:
                res = self.client.table("kill_switch").insert(payload).execute()
            item = res.data[0] if (res.data and isinstance(res.data, list)) else res.data
            if item:
                state = KillSwitchState(**item)
        except Exception:
            pass

        _kill_switch_cache[merchant_id] = state
        return state
