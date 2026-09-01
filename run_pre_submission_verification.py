"""PayFilter — Pre-Submission Evidence Verification Runner.

Runs:
1. Real evaluation on ml/evaluate.ipynb pipeline.
2. Full pytest test suite across all 6 phases.
3. Dependency file audits.
4. Git state inspection.
"""

import os
import sys
import subprocess
import pandas as pd
from pathlib import Path

def run_cmd(cmd, cwd=None):
    print(f"\n>>> Running: {cmd}", flush=True)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    output = res.stdout if res.stdout else res.stderr
    print(output, flush=True)
    return res.returncode, output

def main():
    print("=" * 80)
    print("PAYFILTER PRE-SUBMISSION VERIFICATION PASS")
    print("=" * 80)

    # 1. Real Evaluation Metrics
    print("\n--- [1] REAL ML EVALUATION METRICS ---")
    run_cmd(f'"{sys.executable}" run_eval_metrics.py')

    # 2. Full Test Suite (pytest -v)
    print("\n--- [2] FULL PYTEST TEST SUITE ---")
    run_cmd(f'"{sys.executable}" -m pytest -v')

    # 3. Dependency Audit Check
    print("\n--- [3] DEPENDENCY FILES VERIFICATION ---")
    backend_req = Path("backend/requirements.txt")
    print(f"Backend requirements.txt exists: {backend_req.exists()} ({len(backend_req.read_text().splitlines())} pinned packages)")
    print(backend_req.read_text())

    # 4. Git State Inspection
    print("\n--- [4] GIT STATE INSPECTION ---")
    run_cmd("git log --oneline -10")
    run_cmd("git tag -l")
    run_cmd("git status")
    run_cmd("git remote get-url origin")

if __name__ == "__main__":
    main()
