"""Model Training, Serialization, and Tamper-Evident Integrity Layer for PayFilter.

Trains an IsolationForest model on chronological, time-split synthetic transactions,
computes cryptographic SHA-256 integrity digests, and ensures tamper-evident model loading.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score

from ml.features import FEATURE_COLUMNS, extract_features


class SecurityError(Exception):
    """Raised when model file integrity check fails (e.g. SHA-256 mismatch or tampering)."""
    pass


def compute_file_sha256(file_path: Path | str) -> str:
    """Computes the SHA-256 cryptographic digest of a file.

    Args:
        file_path: Path to the target file.

    Returns:
        str: Hexadecimal SHA-256 hash string.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_model_integrity(
    model_path: Path | str,
    metadata_path: Path | str,
) -> bool:
    """Verifies that the serialized model file matches the SHA-256 hash in metadata.

    Args:
        model_path: Path to the serialized model file (.pkl).
        metadata_path: Path to the model metadata file (.json).

    Returns:
        bool: True if verification succeeds.

    Raises:
        SecurityError: If the computed hash does not match metadata or metadata is invalid.
        FileNotFoundError: If either file is missing.
    """
    model_p = Path(model_path)
    meta_p = Path(metadata_path)

    if not model_p.exists():
        raise FileNotFoundError(f"Model file not found at: {model_p}")
    if not meta_p.exists():
        raise FileNotFoundError(f"Metadata file not found at: {meta_p}")

    with open(meta_p, "r", encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except Exception as e:
            raise SecurityError(f"Failed to parse metadata JSON: {e}") from e

    expected_hash = meta.get("model_hash")
    if not expected_hash:
        raise SecurityError("Model metadata is missing 'model_hash' field.")

    actual_hash = compute_file_sha256(model_p)
    if actual_hash.lower() != expected_hash.lower():
        raise SecurityError(
            f"Model integrity verification failed! Expected SHA-256: {expected_hash}, "
            f"but computed: {actual_hash}. Model file may be corrupted or tampered with."
        )

    return True


def load_secure_model(
    model_path: Optional[Path | str] = None,
    metadata_path: Optional[Path | str] = None,
) -> Tuple[IsolationForest, Dict[str, Any]]:
    """Loads an IsolationForest model after verifying its SHA-256 tamper-evident integrity.

    Args:
        model_path: Path to the model pickle file.
        metadata_path: Path to the metadata JSON file.

    Returns:
        Tuple[IsolationForest, Dict[str, Any]]: Loaded model instance and metadata dict.

    Raises:
        SecurityError: If SHA-256 integrity verification fails.
    """
    base_dir = Path(__file__).resolve().parent
    if model_path is None:
        model_path = base_dir / "models" / "isolation_forest.pkl"
    else:
        model_path = Path(model_path)

    if metadata_path is None:
        metadata_path = base_dir / "models" / "model_metadata.json"
    else:
        metadata_path = Path(metadata_path)

    # Perform strict cryptographic verification
    verify_model_integrity(model_path, metadata_path)

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    model = joblib.load(model_path)
    return model, meta


def time_based_train_test_split(
    df: pd.DataFrame,
    features_df: pd.DataFrame,
    train_ratio: float = 0.80,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame, pd.DataFrame]:
    """Splits dataset strictly by chronological timestamp.

    Guarantees no lookahead leakage between training and evaluation windows.

    Args:
        df: Raw transactions dataframe.
        features_df: Precomputed features dataframe.
        train_ratio: Fraction of the chronological time range used for training (e.g. 0.80).

    Returns:
        Tuple: (X_train, X_test, y_train, y_test, df_train, df_test)
    """
    df_sorted = df.copy()
    df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
    df_sorted = df_sorted.sort_values(by="timestamp").reset_index(drop=True)

    min_t = df_sorted["timestamp"].min()
    max_t = df_sorted["timestamp"].max()
    time_span = max_t - min_t
    split_cutoff = min_t + (time_span * train_ratio)

    train_mask = df_sorted["timestamp"] <= split_cutoff
    test_mask = ~train_mask

    df_train = df_sorted[train_mask].copy()
    df_test = df_sorted[test_mask].copy()

    X_train = features_df.iloc[df_train.index].copy().reset_index(drop=True)
    X_test = features_df.iloc[df_test.index].copy().reset_index(drop=True)

    y_train = df_train["label"].reset_index(drop=True)
    y_test = df_test["label"].reset_index(drop=True)

    return X_train, X_test, y_train, y_test, df_train, df_test


def train_isolation_forest(
    X_train: pd.DataFrame,
    contamination: float = 0.015,
    random_state: int = 42,
    n_estimators: int = 150,
) -> IsolationForest:
    """Trains an Isolation Forest anomaly detector.

    Args:
        X_train: Training feature matrix.
        contamination: Assumed real-world anomaly rate (e.g. 0.015 = 1.5%).
        random_state: Fixed random seed for determinism.
        n_estimators: Number of isolation trees in ensemble.

    Returns:
        IsolationForest: Fitted model instance.
    """
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples="auto",
        contamination=contamination,
        random_state=random_state,
        n_jobs=1,
    )
    model.fit(X_train[FEATURE_COLUMNS])
    return model


def evaluate_model_predictions(
    model: IsolationForest,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, float]:
    """Generates anomaly predictions and evaluates performance metrics.

    In scikit-learn IsolationForest, predict() returns -1 for anomaly, +1 for normal.
    We map: -1 -> 1 (anomaly), +1 -> 0 (normal).
    """
    raw_preds = model.predict(X_test[FEATURE_COLUMNS])
    binary_preds = np.where(raw_preds == -1, 1, 0)

    precision = float(precision_score(y_test, binary_preds, zero_division=0))
    recall = float(recall_score(y_test, binary_preds, zero_division=0))
    f1 = float(f1_score(y_test, binary_preds, zero_division=0))

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "total_test_samples": len(y_test),
        "actual_anomalies": int(y_test.sum()),
        "predicted_anomalies": int(binary_preds.sum()),
    }


def train_and_save_pipeline(
    data_path: Optional[Path | str] = None,
    output_dir: Optional[Path | str] = None,
    contamination: float = 0.015,
    random_seed: int = 42,
    train_ratio: float = 0.80,
) -> Tuple[Path, Path, Dict[str, Any]]:
    """Complete end-to-end model training, evaluation, and secure serialization pipeline.

    Args:
        data_path: Path to synthetic_transactions.csv.
        output_dir: Directory to save model and metadata.
        contamination: Assumed real-world contamination parameter.
        random_seed: Fixed seed for reproducibility.
        train_ratio: Chronological split ratio.

    Returns:
        Tuple[Path, Path, Dict[str, Any]]: Paths to model.pkl, metadata.json, and metadata dict.
    """
    base_dir = Path(__file__).resolve().parent
    if data_path is None:
        data_path = base_dir / "data" / "synthetic_transactions.csv"
    else:
        data_path = Path(data_path)

    if output_dir is None:
        output_dir = base_dir / "models"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    model_file = output_dir / "isolation_forest.pkl"
    metadata_file = output_dir / "model_metadata.json"

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at: {data_path}. Run generate_synthetic_data.py first.")

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    dataset_hash = compute_file_sha256(data_path)

    print("Extracting leakage-safe features...")
    features_df = extract_features(df)

    print(f"Performing time-based train/test split ({train_ratio*100:.0f}% / {(1-train_ratio)*100:.0f}%)...")
    X_train, X_test, y_train, y_test, df_train, df_test = time_based_train_test_split(
        df, features_df, train_ratio=train_ratio
    )

    training_set_anomaly_rate = float(y_train.mean())
    print(f"Training samples: {len(X_train)} (Anomaly rate: {training_set_anomaly_rate:.4f})")
    print(f"Test samples: {len(X_test)} (Anomaly rate: {y_test.mean():.4f})")
    print(f"Model contamination setting (assumed real-world): {contamination:.4f}")

    print("Training IsolationForest model...")
    model = train_isolation_forest(
        X_train,
        contamination=contamination,
        random_state=random_seed,
    )

    eval_metrics = evaluate_model_predictions(model, X_test, y_test)
    print(f"Evaluation metrics on test set: Precision={eval_metrics['precision']:.4f}, "
          f"Recall={eval_metrics['recall']:.4f}, F1={eval_metrics['f1']:.4f}")

    # Serialize model
    print(f"Saving model to {model_file}...")
    joblib.dump(model, model_file, compress=3)

    # Compute model SHA-256 hash
    model_hash = compute_file_sha256(model_file)

    # Create metadata
    metadata = {
        "model_version": "1.0.0",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_hash": dataset_hash,
        "model_hash": model_hash,
        "contamination_param": contamination,
        "training_set_anomaly_rate": round(training_set_anomaly_rate, 4),
        "feature_list": FEATURE_COLUMNS,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": eval_metrics,
    }

    print(f"Saving model metadata to {metadata_file}...")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Verify integrity immediately
    verify_model_integrity(model_file, metadata_file)
    print("Integrity verification passed successfully!")

    return model_file, metadata_file, metadata


def main() -> None:
    """CLI entrypoint for training."""
    parser = argparse.ArgumentParser(description="Train PayFilter Isolation Forest Anomaly Model")
    parser.add_argument("--data", type=str, default=None, help="Path to synthetic_transactions.csv")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for model artifacts")
    parser.add_argument("--contamination", type=float, default=0.015, help="Assumed real-world contamination")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--train-ratio", type=float, default=0.80, help="Train time ratio")

    args = parser.parse_args()
    train_and_save_pipeline(
        data_path=args.data,
        output_dir=args.output_dir,
        contamination=args.contamination,
        random_seed=args.seed,
        train_ratio=args.train_ratio,
    )


if __name__ == "__main__":
    main()
