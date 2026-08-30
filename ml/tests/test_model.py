"""Unit tests for model training, time-based split, and tamper-evident security layer."""

import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from ml.features import extract_features
from ml.generate_synthetic_data import generate_synthetic_transactions
from ml.train_model import (
    SecurityError,
    compute_file_sha256,
    load_secure_model,
    time_based_train_test_split,
    train_and_save_pipeline,
    train_isolation_forest,
    verify_model_integrity,
)


@pytest.fixture(scope="module")
def small_synthetic_dataset(tmp_path_factory) -> Path:
    """Generates a small temporary synthetic dataset for fast model testing."""
    tmp_dir = tmp_path_factory.mktemp("ml_test_data")
    csv_path = tmp_dir / "test_transactions.csv"
    df = generate_synthetic_transactions(
        target_normal=1000,
        target_anomalous=60,
        num_days=15,
        random_seed=42,
    )
    df.to_csv(csv_path, index=False)
    return csv_path


def test_time_based_split_chronology(small_synthetic_dataset):
    """Verify time-based train/test split partitions data by timestamp without overlap."""
    df = pd.read_csv(small_synthetic_dataset)
    features_df = extract_features(df)

    X_train, X_test, y_train, y_test, df_train, df_test = time_based_train_test_split(
        df, features_df, train_ratio=0.80
    )

    assert len(X_train) + len(X_test) == len(df)
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)

    # Max train timestamp must be <= min test timestamp
    max_train_ts = pd.to_datetime(df_train["timestamp"]).max()
    min_test_ts = pd.to_datetime(df_test["timestamp"]).min()
    assert max_train_ts <= min_test_ts, "Train timestamps must precede test timestamps"


def test_train_and_save_pipeline_metadata(small_synthetic_dataset, tmp_path):
    """Verify training pipeline creates valid model, metadata, and hashes."""
    models_dir = tmp_path / "models"
    model_file, metadata_file, meta = train_and_save_pipeline(
        data_path=small_synthetic_dataset,
        output_dir=models_dir,
        contamination=0.015,
        random_seed=42,
    )

    assert model_file.exists()
    assert metadata_file.exists()

    with open(metadata_file, "r", encoding="utf-8") as f:
        meta_loaded = json.load(f)

    # Check required fields
    required_keys = [
        "model_version",
        "training_timestamp",
        "dataset_hash",
        "model_hash",
        "contamination_param",
        "training_set_anomaly_rate",
        "feature_list",
    ]
    for key in required_keys:
        assert key in meta_loaded, f"Metadata missing key: {key}"

    assert meta_loaded["contamination_param"] == 0.015
    # Actual rate in small dataset is ~60 / 1060 ~= 0.056
    assert meta_loaded["training_set_anomaly_rate"] > 0

    # Clean verification passes
    assert verify_model_integrity(model_file, metadata_file) is True

    # Loading clean model succeeds
    model, meta_dict = load_secure_model(model_file, metadata_file)
    assert model is not None
    assert meta_dict["model_version"] == "1.0.0"


def test_deliberate_model_tamper_detection(small_synthetic_dataset, tmp_path):
    """Security test: Deliberately flip bytes in the model file and verify SecurityError is raised."""
    models_dir = tmp_path / "tamper_test_models"
    model_file, metadata_file, _ = train_and_save_pipeline(
        data_path=small_synthetic_dataset,
        output_dir=models_dir,
        contamination=0.015,
        random_seed=42,
    )

    # Clean verification passes
    verify_model_integrity(model_file, metadata_file)

    # Deliberately corrupt 1 byte in the model file
    with open(model_file, "r+b") as f:
        f.seek(64)
        original_byte = f.read(1)
        # Flip the byte
        corrupted_byte = bytes([original_byte[0] ^ 0xFF])
        f.seek(64)
        f.write(corrupted_byte)

    # Verification must fail and raise SecurityError
    with pytest.raises(SecurityError) as exc_info:
        verify_model_integrity(model_file, metadata_file)
    assert "integrity verification failed" in str(exc_info.value).lower()

    # load_secure_model must also refuse to load
    with pytest.raises(SecurityError):
        load_secure_model(model_file, metadata_file)


def test_metadata_tamper_detection(small_synthetic_dataset, tmp_path):
    """Security test: Tampering with the expected hash in metadata causes verification failure."""
    models_dir = tmp_path / "meta_tamper_models"
    model_file, metadata_file, _ = train_and_save_pipeline(
        data_path=small_synthetic_dataset,
        output_dir=models_dir,
        contamination=0.015,
        random_seed=42,
    )

    # Modify metadata with fake hash
    with open(metadata_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["model_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    with pytest.raises(SecurityError):
        verify_model_integrity(model_file, metadata_file)
