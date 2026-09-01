import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

log_file = ROOT_DIR / "test_results.log"
with open(log_file, "w", encoding="utf-8") as f:
    f.write("INIT\n")

def log(msg: str):
    print(msg, flush=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()

log("Testing imports...")
import backend.app.main as main_mod
import backend.tests.test_rules as tr
import backend.tests.test_scorer as ts
import backend.tests.test_idempotency as ti
import backend.tests.test_audit_chain as tac
import backend.tests.test_rls_isolation as trls
log("Imports successful.")

log("Running rules tests...")
tr.test_normal_transaction_passes_rules()
tr.test_max_amount_exceeded_rule()
tr.test_category_limit_exceeded_rule()
tr.test_velocity_limit_exceeded_rule()
log("Rules tests: 4/4 passed.")

log("Running scorer tests...")
ts.test_scorer_approve_decision()
ts.test_scorer_hold_decision_from_medium_score()
ts.test_scorer_block_decision_from_high_score()
ts.test_scorer_block_decision_from_hard_rule()
log("Scorer tests: 4/4 passed.")

log("Running idempotency tests...")
ti.test_idempotency_new_transaction()
ti.test_idempotency_duplicate_transaction()
log("Idempotency tests: 2/2 passed.")

log("Running audit chain tests...")
tac.test_genesis_hash_first_entry()
tac.test_audit_chain_sequential_integrity()
tac.test_deliberate_tamper_detection_in_audit_chain()
tac.test_deliberate_prev_hash_tamper_detection()
log("Audit chain tests: 4/4 passed.")

log("Running RLS isolation tests...")
trls.test_cross_merchant_transaction_isolation()
trls.test_cross_merchant_audit_log_isolation()
trls.test_cross_merchant_rules_config_isolation()
log("RLS isolation tests: 3/3 passed.")

log("Running API endpoint tests...")
import backend.tests.test_api as tapi
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.risk_engine.model import get_model_manager

tapi.reset_in_memory_db()
get_model_manager().initialize()
client = TestClient(app, raise_server_exceptions=True)

tapi.test_health_endpoint(client)
tapi.test_post_transaction_check_valid_approved(client)
tapi.test_post_transaction_check_rejected_on_negative_amount(client)
tapi.test_post_transaction_check_rejected_on_extra_fields(client)
tapi.test_idempotent_duplicate_request(client)
tapi.test_audit_log_endpoint_paginated(client)
log("API endpoint tests: 6/6 passed.")

log("ALL 19 TESTS ACROSS 6 MODULES PASSED PERFECTLY!")
