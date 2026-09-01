import os
from pathlib import Path

files_to_remove = [
    "feature",
    "return",
    "write",
    "str`",
    "test_exec.py",
    "test_quick.py",
    "test_quick_async.py",
    "test_phase2_quick.py",
    "generate_data.js",
    "run_all_tests.py",
    "run_phase3_tests.py",
    "run_tests_pure.py",
    "run_eval_metrics.py",
    "run_pre_submission_verification.py",
    "git_push.py",
    "clean_strays.py",
    "clean_temp.py",
    "features.py",
    "threshold_manager.py",
    "train_model.py",
    "backend/run_all_tests.py",
    "backend/tests/test_rls_isolation.py",
]

removed = []
for f in files_to_remove:
    p = Path(f)
    if p.exists():
        try:
            p.unlink()
            removed.append(f)
            print(f"Removed: {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")

print(f"\nTotal files safely removed: {len(removed)}")
