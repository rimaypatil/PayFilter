"""Test runner for PayFilter Phase 2 backend and Phase 1 ML test suites."""

import sys
from pathlib import Path
import pytest

# Ensure sys.path contains workspace root and backend
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for path in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

def run_tests():
    print("=" * 60, flush=True)
    print("RUNNING PAYFILTER COMPLETE TEST SUITE", flush=True)
    print(f"Root: {ROOT_DIR}", flush=True)
    print(f"Python: {sys.version}", flush=True)
    print("=" * 60, flush=True)

    test_dirs = [
        str(BACKEND_DIR / "tests"),
    ]

    args = [
        "-v",
        "-s",
        "-p", "no:langsmith",
        "-p", "no:cov",
        *test_dirs
    ]

    exit_code = pytest.main(args)
    print("=" * 60, flush=True)
    print(f"BACKEND TEST RUN COMPLETED WITH EXIT CODE: {exit_code}", flush=True)
    print("=" * 60, flush=True)
    return exit_code

if __name__ == "__main__":
    code = run_tests()
    sys.exit(code)
