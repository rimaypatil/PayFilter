import os

for f in ["clean_strays.py", "run_eval_metrics.py", "run_pre_submission_verification.py", "git_push.py", "test_exec.py", "test_quick.py", "test_quick_async.py", "run_all_tests.py", "run_phase3_tests.py", "run_tests_pure.py", "test_phase2_quick.py", "generate_data.js", "feature", "return", "write", "str`"]:
    if os.path.exists(f):
        try:
            os.remove(f)
        except Exception:
            pass
