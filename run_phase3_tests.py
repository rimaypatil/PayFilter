import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import traceback
from fastapi.testclient import TestClient
from backend.app.main import app

def run_tests():
    total_passed = 0
    total_failed = 0

    test_modules = [
        ("1. Auth & API Keys", "backend.tests.test_auth"),
        ("2. RBAC Permissions", "backend.tests.test_permissions"),
        ("3. Confirmations Workflow", "backend.tests.test_confirmations"),
        ("4. Kill Switch & Step-Up", "backend.tests.test_kill_switch"),
        ("5. Timeout Handler", "backend.tests.test_timeout_handler"),
        ("6. Multi-Tenant RLS with Auth", "backend.tests.test_rls_with_auth"),
        ("7. Risk Rules", "backend.tests.test_rules"),
        ("8. Unified Scorer", "backend.tests.test_scorer"),
        ("9. Idempotency", "backend.tests.test_idempotency"),
        ("10. Cryptographic Audit Chain", "backend.tests.test_audit_chain"),
        ("11. API Endpoints", "backend.tests.test_api"),
    ]

    from backend.app.risk_engine.model import get_model_manager
    get_model_manager().initialize()
    app.state.disable_scheduler = True
    client = TestClient(app, raise_server_exceptions=True)

    for title, mod_name in test_modules:
        print(f"\n--- {title} ({mod_name}) ---", flush=True)
        try:
            __import__(mod_name)
            mod = sys.modules[mod_name]
        except Exception as e:
            print(f"  [ERROR] Failed to import {mod_name}: {e}", flush=True)
            traceback.print_exc()
            total_failed += 1
            continue

        test_funcs = [attr for attr in dir(mod) if attr.startswith("test_")]

        for fn_name in test_funcs:
            fn = getattr(mod, fn_name)
            if not callable(fn):
                continue
            try:
                # Check if setup_db or clean_db fixture exists
                if hasattr(mod, "setup_db") and callable(getattr(mod, "setup_db")):
                    mod.setup_db()
                elif hasattr(mod, "clean_db") and callable(getattr(mod, "clean_db")):
                    mod.clean_db()

                # Call test function with needed arguments
                import inspect
                sig = inspect.signature(fn)
                params = sig.parameters
                args = {}
                if "client" in params:
                    args["client"] = client
                if "merchant_auth" in params:
                    if hasattr(mod, "create_merchant_auth"):
                        args["merchant_auth"] = mod.create_merchant_auth()
                    else:
                        args["merchant_auth"] = mod.merchant_auth()

                fn(**args)
                print(f"  [PASS] {fn_name}", flush=True)
                total_passed += 1
            except Exception as e:
                print(f"  [FAIL] {fn_name}: {e}", flush=True)
                traceback.print_exc()
                total_failed += 1

    print("\n" + "=" * 50, flush=True)
    print(f"RESULTS: {total_passed} PASSED, {total_failed} FAILED", flush=True)
    print("=" * 50, flush=True)
    return total_failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
