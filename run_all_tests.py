import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import pytest

if __name__ == "__main__":
    exit_code = pytest.main(["-v", "backend/tests", "ml/tests"])
    sys.exit(exit_code)
