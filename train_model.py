"""Root proxy for ml.train_model to support direct root imports."""

from ml.train_model import (
    SecurityError,
    compute_file_sha256,
    load_secure_model,
    time_based_train_test_split,
    train_and_save_pipeline,
    train_isolation_forest,
    verify_model_integrity,
)

__all__ = [
    "SecurityError",
    "compute_file_sha256",
    "load_secure_model",
    "time_based_train_test_split",
    "train_and_save_pipeline",
    "train_isolation_forest",
    "verify_model_integrity",
]
