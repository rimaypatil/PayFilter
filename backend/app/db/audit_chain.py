"""Tamper-evident cryptographic audit chain for PayFilter.

Implements SHA-256 hash chaining over sequential audit log records.
Provides verification routines to detect any unauthorized data modifications.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

GENESIS_HASH: str = "0" * 64


def canonical_serialize(data: Dict[str, Any]) -> str:
    """Serializes a dictionary deterministically into sorted JSON format."""
    return json.dumps(data, sort_keys=True, default=str)


def hash_row(row_data: Dict[str, Any], prev_hash: str) -> str:
    """Computes SHA-256 digest of row data concatenated with the previous row hash.

    Args:
        row_data: Dictionary containing row fields (transaction_id, merchant_id, action, actor, etc.).
                  Excludes 'row_hash' and 'id' to prevent circular hashing.
        prev_hash: SHA-256 hash of previous row in the merchant's chain (or GENESIS_HASH).

    Returns:
        str: 64-character hexadecimal SHA-256 hash.
    """
    # Filter out non-payload keys to ensure canonical determinism
    payload = {
        "transaction_id": str(row_data.get("transaction_id") or ""),
        "merchant_id": str(row_data.get("merchant_id") or ""),
        "action": str(row_data.get("action") or ""),
        "actor": str(row_data.get("actor") or "system"),
        "created_at": str(row_data.get("created_at") or ""),
        "prev_hash": str(prev_hash),
    }

    serialized = canonical_serialize(payload)
    hasher = hashlib.sha256()
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


def verify_chain_entries(rows: List[Dict[str, Any]]) -> bool:
    """Verifies a sequential list of audit rows for cryptographic chain integrity.

    Args:
        rows: List of audit log records ordered chronologically (oldest first).

    Returns:
        bool: True if every row's prev_hash matches the prior row's row_hash,
              and recomputed hash equals stored row_hash. False if tampered.
    """
    if not rows:
        return True

    expected_prev = GENESIS_HASH

    for row in rows:
        stored_prev = row.get("prev_hash")
        stored_hash = row.get("row_hash")

        # 1. Verify prev_hash link
        if stored_prev != expected_prev:
            return False

        # 2. Recompute hash
        recomputed = hash_row(row, stored_prev)
        if recomputed.lower() != str(stored_hash).lower():
            return False

        # Advance expected prev_hash
        expected_prev = stored_hash

    return True


def verify_chain(merchant_id: str, client: Optional[Any] = None) -> bool:
    """Walks the full audit chain for a merchant from database/repository and confirms integrity.

    Args:
        merchant_id: UUID of the merchant.
        client: Optional Supabase client or repository override.

    Returns:
        bool: True if chain is 100% valid; False if any row was tampered or sequence broken.
    """
    from backend.app.db.repository.audit_repo import AuditRepository

    repo = AuditRepository(client=client)
    rows = repo.get_all_rows_for_merchant(merchant_id)
    return verify_chain_entries(rows)
