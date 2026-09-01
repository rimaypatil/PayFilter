"""Demonstration script showcasing PayFilter Phase 2 backend decision tiers.

Simulates 3 realistic AI-agent transactions:
1. Normal low-risk procurement transaction -> 'approved'
2. Moderate velocity spike with unseen merchant category -> 'held'
3. Rule violation exceeding merchant order cap -> 'blocked'
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.db.audit_chain import verify_chain
from backend.app.risk_engine.model import get_model_manager


def run_demonstration():
    print("=" * 80, flush=True)
    print("PAYFILTER PHASE 2: RISK ENGINE & CRYPTOGRAPHIC AUDIT DEMONSTRATION", flush=True)
    print("=" * 80, flush=True)

    reset_in_memory_db()
    get_model_manager().initialize()
    client = TestClient(app, raise_server_exceptions=True)

    merchant_id = "a0000000-0000-0000-0000-000000000001"

    # Configure merchant rules: max 50,000 INR per order, max 5 txns/min
    rules_repo = RulesRepository()
    rules_repo.upsert_rules_config(
        merchant_id=merchant_id,
        max_amount_per_order=50000.0,
        max_transactions_per_minute=5,
        category_limits={"gaming": 10000.0},
    )

    # Populate customer history with normal baseline transactions
    txns_repo = TransactionsRepository()
    for i in range(5):
        txns_repo.create_transaction({
            "id": f"hist-0000-0000-0000-00000000000{i}",
            "merchant_id": merchant_id,
            "customer_id": "cust_demo_alice",
            "amount": 2500.0,
            "agent_type": "procurement_agent",
            "status": "approved",
            "risk_score": 0.08,
            "reason": {"decision": "approved"},
            "model_version": "1.0.0",
            "created_at": f"2026-08-30T0{i+1}:00:00Z",
        })

    # SCENARIO 1: Normal Low-Risk Transaction (Approved)
    print("\n--- SCENARIO 1: Low-Risk Normal Purchase ---", flush=True)
    payload_normal = {
        "transaction_id": "11111111-aaaa-bbbb-cccc-111111111111",
        "merchant_id": merchant_id,
        "customer_id": "cust_demo_alice",
        "amount": 2600.00,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    res1 = client.post("/transactions/check", json=payload_normal)
    print(f"Request: Amount={payload_normal['amount']}, Category={payload_normal['merchant_category']}", flush=True)
    print(f"HTTP Status: {res1.status_code}", flush=True)
    print(f"Response: {json.dumps(res1.json(), indent=2)}", flush=True)

    # SCENARIO 2: Moderate Anomaly / Shift (Held for Review)
    print("\n--- SCENARIO 2: Unusual Amount & Unseen Category (Medium Risk) ---", flush=True)
    payload_held = {
        "transaction_id": "22222222-aaaa-bbbb-cccc-222222222222",
        "merchant_id": merchant_id,
        "customer_id": "cust_demo_alice",
        "amount": 12500.00,  # 5x normal average
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "luxury_crypto",
        "agent_type": "procurement_agent",
    }
    res2 = client.post("/transactions/check", json=payload_held)
    print(f"Request: Amount={payload_held['amount']} (5x baseline), Category={payload_held['merchant_category']}", flush=True)
    print(f"HTTP Status: {res2.status_code}", flush=True)
    print(f"Response: {json.dumps(res2.json(), indent=2)}", flush=True)

    # SCENARIO 3: Hard Rule Exceeded (Blocked Immediately)
    print("\n--- SCENARIO 3: Hard Rule Violation (Exceeds Merchant Cap) ---", flush=True)
    payload_blocked = {
        "transaction_id": "33333333-aaaa-bbbb-cccc-333333333333",
        "merchant_id": merchant_id,
        "customer_id": "cust_demo_alice",
        "amount": 75000.00,  # Exceeds 50,000 cap
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "electronics",
        "agent_type": "procurement_agent",
    }
    res3 = client.post("/transactions/check", json=payload_blocked)
    print(f"Request: Amount={payload_blocked['amount']} (Max cap is 50,000)", flush=True)
    print(f"HTTP Status: {res3.status_code}", flush=True)
    print(f"Response: {json.dumps(res3.json(), indent=2)}", flush=True)

    # SCENARIO 4: Idempotency Replay
    print("\n--- SCENARIO 4: Idempotency Check (Duplicate Transaction Submission) ---", flush=True)
    res_replay = client.post("/transactions/check", json=payload_normal)
    print(f"Re-submitting Transaction ID: {payload_normal['transaction_id']}", flush=True)
    print(f"Response (Identical Cached Decision): {json.dumps(res_replay.json(), indent=2)}", flush=True)

    # SCENARIO 5: Verify Cryptographic Audit Trail
    print("\n--- SCENARIO 5: Cryptographic Audit Trail Verification ---", flush=True)
    is_chain_valid = verify_chain(merchant_id=merchant_id)
    print(f"Audit Log Chain Integrity for Merchant {merchant_id}: {'VALID (100% Intact)' if is_chain_valid else 'TAMPERED'}", flush=True)

    # Fetch Audit Log Entries
    audit_res = client.get(f"/audit-log?merchant_id={merchant_id}&page=1&page_size=10")
    print(f"Audit Log Entries Count: {audit_res.json()['total']}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    run_demonstration()
