"""Direct Python test runner executing each test suite function explicitly."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

passed = 0
failed = 0

def run_test_func(name, fn, *args):
    global passed, failed
    try:
        fn(*args)
        print(f"  [PASS] {name}", flush=True)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        failed += 1

print("--- 1. Testing Risk Rules (backend.tests.test_rules) ---", flush=True)
import backend.tests.test_rules as tr
run_test_func("test_normal_transaction_passes_rules", tr.test_normal_transaction_passes_rules)
run_test_func("test_max_amount_exceeded_rule", tr.test_max_amount_exceeded_rule)
run_test_func("test_category_limit_exceeded_rule", tr.test_category_limit_exceeded_rule)
run_test_func("test_velocity_limit_exceeded_rule", tr.test_velocity_limit_exceeded_rule)

print("--- 2. Testing Scorer (backend.tests.test_scorer) ---", flush=True)
import backend.tests.test_scorer as ts
run_test_func("test_scorer_approve_decision", ts.test_scorer_approve_decision)
run_test_func("test_scorer_hold_decision_from_medium_score", ts.test_scorer_hold_decision_from_medium_score)
run_test_func("test_scorer_block_decision_from_high_score", ts.test_scorer_block_decision_from_high_score)
run_test_func("test_scorer_block_decision_from_hard_rule", ts.test_scorer_block_decision_from_hard_rule)

print("--- 3. Testing Idempotency (backend.tests.test_idempotency) ---", flush=True)
import backend.tests.test_idempotency as ti
run_test_func("test_idempotency_new_transaction", ti.test_idempotency_new_transaction)
run_test_func("test_idempotency_duplicate_transaction", ti.test_idempotency_duplicate_transaction)

print("--- 4. Testing Audit Chain & Tamper Detection (backend.tests.test_audit_chain) ---", flush=True)
import backend.tests.test_audit_chain as tac
run_test_func("test_genesis_hash_first_entry", tac.test_genesis_hash_first_entry)
run_test_func("test_audit_chain_sequential_integrity", tac.test_audit_chain_sequential_integrity)
run_test_func("test_deliberate_tamper_detection_in_audit_chain", tac.test_deliberate_tamper_detection_in_audit_chain)
run_test_func("test_deliberate_prev_hash_tamper_detection", tac.test_deliberate_prev_hash_tamper_detection)

print("--- 5. Testing RLS Multi-Tenant Isolation (backend.tests.test_rls_isolation) ---", flush=True)
import backend.tests.test_rls_isolation as trls
run_test_func("test_cross_merchant_transaction_isolation", trls.test_cross_merchant_transaction_isolation)
run_test_func("test_cross_merchant_audit_log_isolation", trls.test_cross_merchant_audit_log_isolation)
run_test_func("test_cross_merchant_rules_config_isolation", trls.test_cross_merchant_rules_config_isolation)

print("--- 6. Testing FastAPI Endpoints (backend.tests.test_api) ---", flush=True)
import backend.tests.test_api as tapi
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.risk_engine.model import get_model_manager

tapi.reset_in_memory_db()
get_model_manager().initialize()
client = TestClient(app, raise_server_exceptions=True)

run_test_func("test_health_endpoint", tapi.test_health_endpoint, client)
run_test_func("test_post_transaction_check_valid_approved", tapi.test_post_transaction_check_valid_approved, client)
run_test_func("test_post_transaction_check_rejected_on_negative_amount", tapi.test_post_transaction_check_rejected_on_negative_amount, client)
run_test_func("test_post_transaction_check_rejected_on_extra_fields", tapi.test_post_transaction_check_rejected_on_extra_fields, client)
run_test_func("test_idempotent_duplicate_request", tapi.test_idempotent_duplicate_request, client)
run_test_func("test_audit_log_endpoint_paginated", tapi.test_audit_log_endpoint_paginated, client)

print("--- 7. Testing Auth & JWT Verification (backend.tests.test_auth) ---", flush=True)
import backend.tests.test_auth as tauth
run_test_func("test_missing_jwt_token_returns_401", tauth.test_missing_jwt_token_returns_401, client)
run_test_func("test_expired_jwt_token_returns_401", tauth.test_expired_jwt_token_returns_401, client)
run_test_func("test_tampered_jwt_signature_returns_401", tauth.test_tampered_jwt_signature_returns_401, client)
run_test_func("test_missing_merchant_api_key_returns_401", tauth.test_missing_merchant_api_key_returns_401, client)
run_test_func("test_invalid_merchant_api_key_returns_401", tauth.test_invalid_merchant_api_key_returns_401, client)

print("--- 8. Testing API Key Management & Rotation (backend.tests.test_api_key_management) ---", flush=True)
import backend.tests.test_api_key_management as takm
run_test_func("test_get_api_key_status_admin", takm.test_get_api_key_status_admin, client)
run_test_func("test_get_api_key_status_analyst", takm.test_get_api_key_status_analyst, client)
run_test_func("test_analyst_cannot_rotate_api_key", takm.test_analyst_cannot_rotate_api_key, client)
run_test_func("test_admin_rotate_api_key_lifecycle", takm.test_admin_rotate_api_key_lifecycle, client)
run_test_func("test_unauthenticated_cannot_access_or_rotate", takm.test_unauthenticated_cannot_access_or_rotate, client)

print("--- 9. Testing RBAC & Role Permissions (backend.tests.test_permissions) ---", flush=True)
import backend.tests.test_permissions as tperm
run_test_func("test_analyst_forbidden_from_updating_rules", tperm.test_analyst_forbidden_from_updating_rules, client)
run_test_func("test_admin_can_update_rules", tperm.test_admin_can_update_rules, client)
run_test_func("test_analyst_forbidden_from_rotating_api_key", tperm.test_analyst_forbidden_from_rotating_api_key, client)
run_test_func("test_admin_can_rotate_api_key", tperm.test_admin_can_rotate_api_key, client)
run_test_func("test_analyst_forbidden_from_requesting_kill_switch_otp", tperm.test_analyst_forbidden_from_requesting_kill_switch_otp, client)
run_test_func("test_analyst_can_read_rules_and_audit_log", tperm.test_analyst_can_read_rules_and_audit_log, client)

print(f"\n==========================================", flush=True)
print(f"RESULTS: {passed} PASSED, {failed} FAILED", flush=True)
print(f"==========================================", flush=True)
if failed > 0:
    sys.exit(1)
