"""PayFilter Phase 3 End-to-End Workflow Demonstration.

Demonstrates:
1. Merchant Signup & API Key generation (POST /merchants/signup)
2. Rules Configuration update by Admin (PUT /rules)
3. Transaction scoring with Merchant API Key (POST /transactions/check)
4. Human Analyst Confirmation of a 'held' transaction with JWT (POST /transactions/{id}/confirm)
5. Background Timeout Handler auto-resolution of stale holds (TimeoutHandler)
6. Admin Step-Up OTP generation (POST /kill-switch/request)
7. Kill Switch activation with OTP code (POST /kill-switch/confirm)
8. Immediate blocking of subsequent transactions when kill switch is active
9. Cryptographic Audit Trail verification with JWT scoping (GET /audit-log)
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from datetime import datetime, timedelta, timezone
import json
import jwt
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.db.audit_chain import verify_chain
from backend.app.db.client import reset_in_memory_db
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.main import app
from backend.app.risk_engine.model import get_model_manager
from backend.app.risk_engine.timeout_handler import TimeoutHandler


def create_user_jwt(user_id: str, merchant_id: str, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "aud": settings.SUPABASE_AUDIENCE,
        "email": f"{user_id}@acme-corp.com",
        "merchant_id": merchant_id,
        "role": role,
        "app_metadata": {"merchant_id": merchant_id, "role": role},
        "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def run_phase3_demonstration():
    print("=" * 85, flush=True)
    print("PAYFILTER PHASE 3: AUTH, RBAC, CONFIRMATION WORKFLOW & KILL SWITCH DEMO", flush=True)
    print("=" * 85, flush=True)

    reset_in_memory_db()
    get_model_manager().initialize()
    client = TestClient(app, raise_server_exceptions=True)

    # 1. MERCHANT SIGNUP
    print("\n--- 1. Merchant Registration & API Key Issuance ---", flush=True)
    signup_payload = {
        "name": "Acme Global Procurement Ltd",
        "admin_user_id": "usr_supabase_admin_001",
    }
    res_signup = client.post("/merchants/signup", json=signup_payload)
    signup_data = res_signup.json()
    merchant_id = signup_data["merchant_id"]
    api_key = signup_data["api_key"]
    print(f"Merchant ID: {merchant_id}", flush=True)
    print(f"Generated API Key (Single Reveal): {api_key}", flush=True)

    admin_jwt = create_user_jwt("usr_supabase_admin_001", merchant_id, "admin")
    analyst_jwt = create_user_jwt("usr_supabase_analyst_002", merchant_id, "analyst")

    # 2. ADMIN CONFIGURES RULES
    print("\n--- 2. Admin Configures Merchant Risk Rules (PUT /rules) ---", flush=True)
    rules_payload = {
        "max_amount_per_order": 50000.0,
        "max_transactions_per_minute": 10,
        "category_limits": {"electronics": 40000.0, "crypto": 5000.0},
    }
    res_rules = client.put(
        "/rules",
        json=rules_payload,
        headers={"Authorization": f"Bearer {admin_jwt}"},
    )
    print(f"Updated Rules: {json.dumps(res_rules.json(), indent=2)}", flush=True)

    # Populate customer history
    txns_repo = TransactionsRepository()
    for i in range(3):
        txns_repo.create_transaction({
            "id": f"hist-0000-0000-0000-00000000000{i}",
            "merchant_id": merchant_id,
            "customer_id": "cust_alice",
            "amount": 3000.0,
            "agent_type": "procurement_agent",
            "status": "approved",
            "risk_score": 0.09,
            "reason": {"decision": "approved"},
            "model_version": "1.0.0",
            "created_at": f"2026-08-30T0{i+1}:00:00Z",
        })

    # 3. TRANSACTION EVALUATION (Pre-order API key authenticated)
    print("\n--- 3. Pre-Order Transaction Check (Held for Human Review) ---", flush=True)
    txn_check_payload = {
        "transaction_id": "11111111-2222-3333-4444-555555555555",
        "merchant_id": merchant_id,
        "customer_id": "cust_alice",
        "amount": 18000.0,  # 6x baseline average -> triggers medium risk hold
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merchant_category": "crypto",
        "agent_type": "procurement_agent",
    }
    res_check = client.post(
        "/transactions/check",
        json=txn_check_payload,
        headers={"X-API-Key": api_key},
    )
    check_data = res_check.json()
    print(f"Status: {check_data['status']}", flush=True)
    print(f"Risk Score: {check_data['risk_score']}", flush=True)
    print(f"Reason: {json.dumps(check_data['reason'], indent=2)}", flush=True)

    # 4. HUMAN CONFIRMATION WORKFLOW
    print("\n--- 4. Analyst Human Confirmation (POST /transactions/{id}/confirm) ---", flush=True)
    res_confirm = client.post(
        f"/transactions/{txn_check_payload['transaction_id']}/confirm",
        json={"decision": "approve"},
        headers={"Authorization": f"Bearer {analyst_jwt}"},
    )
    print(f"Analyst Approval Response: {json.dumps(res_confirm.json(), indent=2)}", flush=True)

    # 5. TIMEOUT HANDLER AUTO-RESOLUTION
    print("\n--- 5. Timeout Auto-Resolution (Safe Default for Unreviewed Stale Hold) ---", flush=True)
    stale_txn_id = "stale-held-9999-0000-1111-222222222222"
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=240)  # 4 mins old
    txns_repo.create_transaction({
        "id": stale_txn_id,
        "merchant_id": merchant_id,
        "customer_id": "cust_bob",
        "amount": 80000.0,  # Exceeds safe limit -> defaults to blocked
        "agent_type": "procurement_agent",
        "status": "held",
        "risk_score": 0.60,
        "reason": {"decision": "held"},
        "model_version": "1.0.0",
        "created_at": stale_time.isoformat(),
    })
    timeout_handler = TimeoutHandler(transactions_repo=txns_repo)
    resolved = timeout_handler.process_held_timeouts(timeout_seconds=120, large_threshold=25000.0)
    print(f"Auto-resolved stale holds: {json.dumps(resolved, indent=2)}", flush=True)

    # 6. STEP-UP KILL SWITCH FLOW
    print("\n--- 6. Emergency Kill Switch Request & Step-Up OTP ---", flush=True)
    res_otp = client.post(
        "/kill-switch/request",
        headers={"Authorization": f"Bearer {admin_jwt}"},
    )
    otp_data = res_otp.json()
    otp_code = otp_data["code"]
    print(f"Step-up OTP Code: {otp_code} (Expires: {otp_data['expires_at']})", flush=True)

    # 7. EXECUTE KILL SWITCH
    print("\n--- 7. Admin Confirms Kill Switch Activation with OTP ---", flush=True)
    res_kill = client.post(
        "/kill-switch/confirm",
        json={"code": otp_code, "is_active": True, "reason": "Suspected API key compromise"},
        headers={"Authorization": f"Bearer {admin_jwt}"},
    )
    print(f"Kill Switch Status: {json.dumps(res_kill.json(), indent=2)}", flush=True)

    # 8. SUBSEQUENT TRANSACTIONS ARE BLOCKED
    print("\n--- 8. Attempt Transaction Check while Kill Switch is Active ---", flush=True)
    res_blocked_check = client.post(
        "/transactions/check",
        json={
            "transaction_id": "99999999-8888-7777-6666-555555555555",
            "merchant_id": merchant_id,
            "customer_id": "cust_alice",
            "amount": 50.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "merchant_category": "electronics",
            "agent_type": "procurement_agent",
        },
        headers={"X-API-Key": api_key},
    )
    print(f"Immediate Verdict: {json.dumps(res_blocked_check.json(), indent=2)}", flush=True)

    # 9. AUDIT TRAIL VERIFICATION
    print("\n--- 9. Cryptographic Audit Chain Verification ---", flush=True)
    is_valid = verify_chain(merchant_id=merchant_id)
    print(f"Cryptographic Audit Log Integrity for {merchant_id}: {'100% VALID & INTACT' if is_valid else 'TAMPERED'}", flush=True)

    res_audit = client.get("/audit-log", headers={"Authorization": f"Bearer {analyst_jwt}"})
    print(f"Total Audit Entries Recorded: {res_audit.json()['total']}", flush=True)
    print("=" * 85, flush=True)


if __name__ == "__main__":
    run_phase3_demonstration()
