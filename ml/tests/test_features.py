"""Unit tests for leakage-safe feature engineering in PayFilter."""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from ml.features import (
    FEATURE_COLUMNS,
    extract_features,
    extract_single_transaction_features,
)


@pytest.fixture
def sample_raw_transactions() -> pd.DataFrame:
    """Constructs a deterministic sequence of transactions across multiple customers."""
    records = [
        {
            "transaction_id": "txn_001",
            "customer_id": "cust_101",
            "merchant_id": "merch_001",
            "amount": 500.0,
            "timestamp": "2026-01-01 10:00:00",
            "merchant_category": "ecommerce",
            "agent_type": "procurement_agent",
        },
        {
            "transaction_id": "txn_002",
            "customer_id": "cust_101",
            "merchant_id": "merch_001",
            "amount": 600.0,
            "timestamp": "2026-01-01 10:30:00",
            "merchant_category": "ecommerce",
            "agent_type": "procurement_agent",
        },
        {
            "transaction_id": "txn_003",
            "customer_id": "cust_102",
            "merchant_id": "merch_002",
            "amount": 2000.0,
            "timestamp": "2026-01-01 11:00:00",
            "merchant_category": "travel",
            "agent_type": "personal_assistant",
        },
        {
            "transaction_id": "txn_004",
            "customer_id": "cust_101",
            "merchant_id": "merch_003",
            "amount": 5500.0,
            "timestamp": "2026-01-01 11:15:00",
            "merchant_category": "crypto",
            "agent_type": "automated_scheduler",
        },
    ]
    return pd.DataFrame(records)


def test_feature_columns_and_no_nan(sample_raw_transactions):
    """Verify all expected feature columns exist and contain zero NaN or inf values."""
    feats = extract_features(sample_raw_transactions)

    assert list(feats.columns) == FEATURE_COLUMNS
    assert feats.isna().sum().sum() == 0, "Feature matrix must not contain NaN values"
    assert not np.isinf(feats.values).any(), "Feature matrix must not contain infinite values"
    assert len(feats) == len(sample_raw_transactions)


def test_no_data_leakage_on_future_transaction_injection(sample_raw_transactions):
    """Critical test: Adding future transactions (t > t_N) must NOT alter features for transaction N."""
    base_features = extract_features(sample_raw_transactions)

    # Future transaction occurring later than all existing transactions
    future_txn = pd.DataFrame(
        [
            {
                "transaction_id": "txn_future",
                "customer_id": "cust_101",
                "merchant_id": "merch_999",
                "amount": 99999.0,
                "timestamp": "2026-01-02 12:00:00",
                "merchant_category": "luxury",
                "agent_type": "procurement_agent",
            }
        ]
    )

    augmented_df = pd.concat([sample_raw_transactions, future_txn], ignore_index=True)
    augmented_features = extract_features(augmented_df)

    # Compare features for the original first 4 transactions
    for col in FEATURE_COLUMNS:
        np.testing.assert_allclose(
            base_features[col].values,
            augmented_features.iloc[:4][col].values,
            err_msg=f"Feature '{col}' changed after future transaction injection! Lookahead leakage detected.",
        )


def test_customer_historical_average_logic(sample_raw_transactions):
    """Verify customer average amount is computed strictly over prior transactions."""
    feats = extract_features(sample_raw_transactions)

    # First txn for cust_101 (amount=500): fallback is 500
    assert feats.loc[0, "customer_average_amount"] == 500.0
    assert feats.loc[0, "amount_vs_average_ratio"] == 1.0
    assert feats.loc[0, "is_new_merchant_category_for_customer"] == 1.0

    # Second txn for cust_101 (amount=600): prior avg was 500
    assert feats.loc[1, "customer_average_amount"] == 500.0
    assert feats.loc[1, "amount_vs_average_ratio"] == pytest.approx(600.0 / 500.0)
    assert feats.loc[1, "is_new_merchant_category_for_customer"] == 0.0  # ecommerce already seen

    # Third txn for cust_101 (idx=3, amount=5500): prior avg was (500 + 600) / 2 = 550
    assert feats.loc[3, "customer_average_amount"] == 550.0
    assert feats.loc[3, "amount_vs_average_ratio"] == pytest.approx(5500.0 / 550.0)
    assert feats.loc[3, "is_new_merchant_category_for_customer"] == 1.0  # crypto is new


def test_single_transaction_feature_extractor_equivalence():
    """Verify single transaction feature extraction matches batch extraction exactly."""
    history = pd.DataFrame(
        [
            {
                "transaction_id": "txn_001",
                "customer_id": "cust_101",
                "merchant_id": "merch_001",
                "amount": 1000.0,
                "timestamp": "2026-01-01 09:00:00",
                "merchant_category": "saas",
                "agent_type": "procurement_agent",
            }
        ]
    )

    current_txn = {
        "transaction_id": "txn_002",
        "customer_id": "cust_101",
        "merchant_id": "merch_002",
        "amount": 2500.0,
        "timestamp": "2026-01-01 09:15:00",
        "merchant_category": "saas",
        "agent_type": "procurement_agent",
    }

    full_batch_df = pd.concat([history, pd.DataFrame([current_txn])], ignore_index=True)
    batch_features = extract_features(full_batch_df)
    batch_row = batch_features.iloc[1].to_dict()

    single_features = extract_single_transaction_features(current_txn, history)

    for col in FEATURE_COLUMNS:
        assert single_features[col] == pytest.approx(batch_row[col]), f"Mismatch in feature '{col}'"
