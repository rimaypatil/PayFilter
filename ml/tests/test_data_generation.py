"""Unit tests for synthetic data generation in PayFilter."""

import pandas as pd
import pytest

from ml.generate_synthetic_data import (
    MERCHANT_CATEGORIES,
    AGENT_TYPES,
    generate_synthetic_transactions,
)


def test_synthetic_data_generation_counts():
    """Verify total normal and anomalous transaction counts meet requirements."""
    df = generate_synthetic_transactions(
        target_normal=10000,
        target_anomalous=450,
        num_days=45,
        random_seed=42,
    )

    assert len(df) >= 10400, f"Expected >= 10400 transactions, got {len(df)}"

    normal_count = int((df["label"] == 0).sum())
    anom_count = int((df["label"] == 1).sum())

    assert normal_count >= 10000, f"Expected >= 10000 normal transactions, got {normal_count}"
    assert 400 <= anom_count <= 550, f"Expected 400-550 anomalous transactions, got {anom_count}"


def test_synthetic_data_required_columns():
    """Verify all mandatory columns exist with non-null values."""
    df = generate_synthetic_transactions(
        target_normal=500,
        target_anomalous=50,
        num_days=10,
        random_seed=42,
    )

    required_cols = [
        "transaction_id",
        "customer_id",
        "merchant_id",
        "amount",
        "timestamp",
        "merchant_category",
        "agent_type",
        "label",
    ]

    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
        assert df[col].isnull().sum() == 0, f"Column {col} contains unexpected nulls"

    assert (df["amount"] > 0).all(), "All transaction amounts must be positive"
    assert set(df["label"].unique()).issubset({0, 1}), "Labels must be binary (0 or 1)"


def test_all_five_anomaly_types_present():
    """Verify that all five specified anomaly types are synthesized with counts > 0."""
    df = generate_synthetic_transactions(
        target_normal=1000,
        target_anomalous=200,
        num_days=20,
        random_seed=42,
    )

    expected_anomalies = {
        "velocity_spike",
        "repeat_loop",
        "amount_spike",
        "merchant_shift",
        "odd_hour_burst",
    }

    anom_types = set(df[df["label"] == 1]["anomaly_type"].unique())
    for expected_type in expected_anomalies:
        assert expected_type in anom_types, f"Anomaly type '{expected_type}' is missing from synthetic data"
        count = (df["anomaly_type"] == expected_type).sum()
        assert count > 0, f"Anomaly type '{expected_type}' has 0 occurrences"


def test_synthetic_data_determinism():
    """Verify that using the same random seed produces identical datasets."""
    df1 = generate_synthetic_transactions(target_normal=200, target_anomalous=30, random_seed=99)
    df2 = generate_synthetic_transactions(target_normal=200, target_anomalous=30, random_seed=99)

    pd.testing.assert_frame_equal(df1, df2)
