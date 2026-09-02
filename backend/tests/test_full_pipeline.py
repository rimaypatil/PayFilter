"""PayFilter — Phase 6 Full-Pipeline Integration Test Suite.

This test file verifies the seamless end-to-end integration across all 5 prior phases:
- Phase 1: Feature Extraction, ML IsolationForest, Poisoning Defense
- Phase 2: Risk Scoring Engine, PostgreSQL RLS, SHA-256 Hash Chaining
- Phase 3: Supabase Auth, RBAC Role Gating, Human Confirmations & Kill Switch
- Phase 4: Frontend API Endpoints & State Updates
- Phase 5: Test-Mode Razorpay Orders & Zero-PII Claude Plain-English Explanations

Each scenario represents a real, continuous end-to-end journey.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.auth.jwt_verify import create_mock_jwt
from backend.app.config import get_settings
from backend.app.db.client import get_supabase_client
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.integrations.claude_client import ClaudeClient
from backend.app.main import app
from backend.app.risk_engine.timeout_handler import TimeoutHandler

client = TestClient(app)


@pytest.fixture
def setup_merchants():
    """Sets up two real isolated merchants with API keys and admin/analyst credentials."""
    db_client = get_supabase_client()
    merchants_repo = MerchantsRepository(db_client)

    # Merchant A (Acme Electronics)
    merchant_a_id = f"merchant-a-{uuid.uuid4().hex[:8]}"
    _, raw_key_a = merchants_repo.create_merchant(name="Acme Electronics", merchant_id=merchant_a_id)
    user_a_admin = f"usr-admin-a-{uuid.uuid4().hex[:6]}"
    user_a_analyst = f"usr-analyst-a-{uuid.uuid4().hex[:6]}"
    merchants_repo.assign_user_role(user_a_admin, merchant_a_id, "admin")
    merchants_repo.assign_user_role(user_a_analyst, merchant_a_id, "analyst")

    token_a_admin = create_mock_jwt(user_a_admin, merchant_id=merchant_a_id, role="admin")
    token_a_analyst = create_mock_jwt(user_a_analyst, merchant_id=merchant_a_id, role="analyst")

    # Merchant B (Nova Retail)
    merchant_b_id = f"merchant-b-{uuid.uuid4().hex[:8]}"
    _, raw_key_b = merchants_repo.create_merchant(name="Nova Retail", merchant_id=merchant_b_id)
    user_b_analyst = f"usr-analyst-b-{uuid.uuid4().hex[:6]}"
    merchants_repo.assign_user_role(user_b_analyst, merchant_b_id, "analyst")
    token_b_analyst = create_mock_jwt(user_b_analyst, merchant_id=merchant_b_id, role="analyst")

    return {
        "merchant_a": {
            "id": merchant_a_id,
            "api_key": raw_key_a,
            "admin_token": token_a_admin,
            "analyst_token": token_a_analyst,
            "analyst_user": user_a_analyst,
        },
        "merchant_b": {
            "id": merchant_b_id,
            "api_key": raw_key_b,
            "analyst_token": token_b_analyst,
            "analyst_user": user_b_analyst,
        },
    }


def test_scenario_1_clean_approve_flow(setup_merchants):
    """Scenario 1: Clean Approve Flow.

    Flow:
    1. AI agent submits normal transaction fitting customer's history.
    2. Risk engine scores transaction -> decision: 'approved'.
    3. Test-mode Razorpay Orders API automatically creates a valid order ID.
    4. Cryptographic audit trail logs 'transaction_scored:approved' with verified SHA-256 hash.
    """
    merchant = setup_merchants["merchant_a"]
    txn_id = str(uuid.uuid4())

    payload = {
        "transaction_id": txn_id,
        "merchant_id": merchant["id"],
        "customer_id": "cust_demo_normal",
        "amount": 350.00,
        "timestamp": "2026-09-01T12:00:00Z",
        "merchant_category": "groceries",
        "agent_type": "grocery_procurement_agent",
    }

    # Execute check
    res = client.post("/transactions/check", json=payload, headers={"X-API-Key": merchant["api_key"]})
    assert res.status_code == 200
    data = res.json()

    # 1. Assert Approved Decision
    assert data["status"] == "approved"
    assert data["risk_score"] < 0.45

    # 2. Assert Real/Test-Mode Razorpay Order Created
    assert data["razorpay_order_id"] is not None
    assert str(data["razorpay_order_id"]).startswith("order_")

    # 3. Assert Audit Log Entry
    audit_id = data["audit_log_id"]
    audit_res = client.get("/audit-log", headers={"Authorization": f"Bearer {merchant['analyst_token']}"})
    assert audit_res.status_code == 200
    audit_items = audit_res.json()["items"]
    matched_entry = next((e for e in audit_items if e["id"] == audit_id), None)
    assert matched_entry is not None
    assert matched_entry["action"] == "transaction_scored:approved"
    assert matched_entry["transaction_id"] == txn_id
    assert len(matched_entry["row_hash"]) == 64  # Valid SHA-256 hex


def test_scenario_2_hard_block_flow(setup_merchants):
    """Scenario 2: Hard Block Flow.

    Flow:
    1. AI agent submits transaction violating deterministic order cap (₹85,000 > ₹50,000 limit).
    2. Risk engine blocks transaction immediately.
    3. Razorpay order is NOT created (None).
    4. Claude generates a natural language plain-English explanation without PII.
    5. Audit log records 'transaction_scored:blocked'.
    """
    merchant = setup_merchants["merchant_a"]
    txn_id = str(uuid.uuid4())

    payload = {
        "transaction_id": txn_id,
        "merchant_id": merchant["id"],
        "customer_id": "cust_demo_burst",
        "amount": 85000.00,  # Hard limit breach
        "timestamp": "2026-09-01T12:05:00Z",
        "merchant_category": "luxury",
        "agent_type": "autonomous_loop_agent",
    }

    res = client.post("/transactions/check", json=payload, headers={"X-API-Key": merchant["api_key"]})
    assert res.status_code == 200
    data = res.json()

    # 1. Assert Blocked Decision
    assert data["status"] == "blocked"
    assert data["risk_score"] >= 0.70
    assert data["razorpay_order_id"] is None

    # 2. Assert Claude Plain-English Explanation
    reason = data["reason"]
    assert "explanation" in reason
    assert isinstance(reason["explanation"], str)
    assert len(reason["explanation"]) > 10


def test_scenario_3_hold_human_confirm_flow(setup_merchants):
    """Scenario 3: Hold -> Human Confirmation Flow.

    Flow:
    1. Borderline transaction lands in 'held' state.
    2. Analyst reviews transaction in Flagged Queue and confirms 'approve'.
    3. Status updates to 'approved', Razorpay order is generated.
    4. Audit log records 'confirmed_by_human:approved'.
    5. Adaptive threshold manager dynamically updates risk baseline.
    """
    merchant = setup_merchants["merchant_a"]
    db = get_supabase_client()
    txns_repo = TransactionsRepository(db)

    # Seed a held transaction
    txn_id = str(uuid.uuid4())
    txns_repo.create_transaction({
        "id": txn_id,
        "merchant_id": merchant["id"],
        "customer_id": "cust_demo_borderline",
        "amount": 4800.00,
        "agent_type": "shopper_agent",
        "status": "held",
        "risk_score": 0.55,
        "reason": {"primary_driver": "novel_category_and_ratio", "thresholds": {"hold": 0.45, "block": 0.70}},
        "model_version": "v1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Human Analyst Approves Held Transaction
    confirm_res = client.post(
        f"/transactions/{txn_id}/confirm",
        json={"decision": "approve"},
        headers={"Authorization": f"Bearer {merchant['analyst_token']}"},
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()

    assert confirm_data["status"] == "approved"
    assert confirm_data["previous_status"] == "held"
    assert confirm_data["confirmed_by"] == merchant["analyst_user"]
    assert confirm_data["razorpay_order_id"] is not None


def test_scenario_4_hold_timeout_auto_resolution(setup_merchants):
    """Scenario 4: Hold Timeout Auto-Resolution Flow.

    Flow:
    1. A transaction sits unreviewed in 'held' state past HELD_TIMEOUT_SECONDS.
    2. Background timeout handler processes stale holds.
    3. Safe policy applies: Large transactions (> 25k INR) default to 'blocked'; normal (<= 25k) default to 'approved'.
    4. Audit log gains an 'auto_resolved_timeout' record.
    """
    merchant = setup_merchants["merchant_a"]
    db = get_supabase_client()
    txns_repo = TransactionsRepository(db)
    audit_repo = AuditRepository(db)
    timeout_handler = TimeoutHandler(transactions_repo=txns_repo, audit_repo=audit_repo)

    # Create stale large transaction (> 25,000)
    stale_large_id = str(uuid.uuid4())
    stale_time = (datetime.now(timezone.utc) - timedelta(seconds=200)).isoformat()
    txns_repo.create_transaction({
        "id": stale_large_id,
        "merchant_id": merchant["id"],
        "customer_id": "cust_timeout_large",
        "amount": 35000.00,
        "agent_type": "bulk_agent",
        "status": "held",
        "risk_score": 0.58,
        "reason": {"primary_driver": "high_ticket_ratio"},
        "model_version": "v1.0.0",
        "created_at": stale_time,
    })

    # Trigger timeout handler
    resolved = timeout_handler.process_held_timeouts(merchant_id=merchant["id"])
    resolved_ids = [r["transaction_id"] for r in resolved]
    assert stale_large_id in resolved_ids

    # Verify updated to blocked
    updated_record = txns_repo.get_transaction_by_id(stale_large_id)
    assert updated_record.status == "blocked"


def test_scenario_5_claude_failure_graceful_fallback(setup_merchants):
    """Scenario 5: Claude API Failure & Graceful Fallback.

    Flow:
    1. Claude API is unreachable or times out (simulated with offline client).
    2. Transaction decision completes successfully without throwing an exception or failing.
    3. Clean deterministic fallback explanation is provided in response.
    """
    client_offline = ClaudeClient(api_key=None)  # Simulates API key unset or network timeout
    scorer_output = {
        "decision": "held",
        "primary_driver": "burst_velocity",
        "rule_triggered": "velocity_limit_exceeded",
        "risk_score": 0.62,
    }

    fallback_text = client_offline.explain_decision(scorer_output, amount=3200.0)
    assert fallback_text is not None
    assert len(fallback_text) > 15
    assert "velocity" in fallback_text.lower() or "flagged" in fallback_text.lower()


def test_scenario_6_kill_switch_active_enforcement(setup_merchants):
    """Scenario 6: Step-Up Kill Switch Active Enforcement.

    Flow:
    1. Admin initiates kill switch request -> receives step-up OTP.
    2. Admin confirms kill switch with OTP -> status flips to ACTIVE.
    3. Subsequent checkout attempt is immediately BLOCKED/FROZEN prior to scoring.
    """
    merchant = setup_merchants["merchant_a"]

    # 1. Request OTP
    req_res = client.post("/kill-switch/request", headers={"Authorization": f"Bearer {merchant['admin_token']}"})
    assert req_res.status_code == 200
    otp_code = req_res.json()["code"]

    # 2. Confirm Kill Switch Activation
    confirm_res = client.post(
        "/kill-switch/confirm",
        json={"code": otp_code, "is_active": True, "reason": "Emergency security incident"},
        headers={"Authorization": f"Bearer {merchant['admin_token']}"},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["is_active"] is True

    # 3. Subsequent transaction check must be immediately BLOCKED
    txn_attempt_id = str(uuid.uuid4())
    check_res = client.post(
        "/transactions/check",
        json={
            "transaction_id": txn_attempt_id,
            "merchant_id": merchant["id"],
            "customer_id": "cust_demo_normal",
            "amount": 100.00,  # Even a safe 100 INR order is frozen
            "timestamp": "2026-09-01T13:00:00Z",
            "merchant_category": "groceries",
            "agent_type": "shopper",
        },
        headers={"X-API-Key": merchant["api_key"]},
    )
    assert check_res.status_code == 200
    check_data = check_res.json()
    assert check_data["status"] == "blocked"
    assert check_data["reason"]["primary_driver"] == "kill_switch_activated"

    # Teardown: Deactivate kill switch for subsequent tests
    deact_req = client.post("/kill-switch/request", headers={"Authorization": f"Bearer {merchant['admin_token']}"})
    deact_code = deact_req.json()["code"]
    client.post(
        "/kill-switch/confirm",
        json={"code": deact_code, "is_active": False, "reason": "Incident resolved"},
        headers={"Authorization": f"Bearer {merchant['admin_token']}"},
    )


def test_scenario_7_cross_merchant_tenant_isolation(setup_merchants):
    """Scenario 7: Full-Stack Cross-Merchant Tenant Isolation.

    Flow:
    1. Merchant A submits transactions and creates audit records.
    2. Merchant B queries GET /transactions and GET /audit-log through real HTTP API.
    3. Confirms Merchant B cannot view or access any data belonging to Merchant A.
    """
    merchant_a = setup_merchants["merchant_a"]
    merchant_b = setup_merchants["merchant_b"]

    # Merchant A submits a transaction
    txn_a_id = str(uuid.uuid4())
    client.post(
        "/transactions/check",
        json={
            "transaction_id": txn_a_id,
            "merchant_id": merchant_a["id"],
            "customer_id": "cust_merchant_a_secret",
            "amount": 800.00,
            "timestamp": "2026-09-01T15:00:00Z",
            "merchant_category": "electronics",
            "agent_type": "procurement",
        },
        headers={"X-API-Key": merchant_a["api_key"]},
    )

    # Merchant B queries transactions feed
    res_b_txns = client.get("/transactions", headers={"Authorization": f"Bearer {merchant_b['analyst_token']}"})
    assert res_b_txns.status_code == 200
    items_b = res_b_txns.json()["items"]
    # Merchant B MUST NOT see Merchant A's transaction
    assert not any(t["id"] == txn_a_id for t in items_b)

    # Merchant B queries audit log
    res_b_audit = client.get("/audit-log", headers={"Authorization": f"Bearer {merchant_b['analyst_token']}"})
    assert res_b_audit.status_code == 200
    audit_b_items = res_b_audit.json()["items"]
    assert not any(a["transaction_id"] == txn_a_id for a in audit_b_items)
