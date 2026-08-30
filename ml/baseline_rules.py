"""Rules-Only Baseline for PayFilter.

Implements a deterministic, explainable heuristic rule engine used as an evaluation
and benchmarking baseline against machine learning models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union
import numpy as np
import pandas as pd


def evaluate_single_rule_record(
    features: Union[Dict[str, float], pd.Series],
) -> Tuple[int, List[str]]:
    """Evaluates baseline heuristic rules on a single feature record.

    Args:
        features: Dictionary or Series containing feature values.

    Returns:
        Tuple[int, List[str]]: (prediction [0 or 1], list of triggered rule names).
    """
    amount = float(features.get("amount", 0.0))
    cust_avg = float(features.get("customer_average_amount", 0.0))
    txns_1h = float(features.get("transactions_last_hour", 0.0))
    is_new_cat = float(features.get("is_new_merchant_category_for_customer", 0.0))
    time_since_prev = float(features.get("time_since_previous_transaction", 86400.0))
    hour_dev = float(features.get("hour_of_day_deviation", 0.0))

    triggered_rules: List[str] = []

    # Rule 1: Extreme Amount Spike (amount > 8x customer average)
    if cust_avg > 0 and amount > (cust_avg * 8.0):
        triggered_rules.append("RULE_AMOUNT_SPIKE_8X")

    # Rule 2: High Velocity (more than 5 transactions in the last hour)
    if txns_1h > 5:
        triggered_rules.append("RULE_VELOCITY_SPIKE_1H")

    # Rule 3: High-Value Merchant Shift (unseen category with > 3x average amount)
    if is_new_cat == 1.0 and cust_avg > 0 and amount > (cust_avg * 3.0):
        triggered_rules.append("RULE_NEW_MERCHANT_CATEGORY_HIGH_AMOUNT")

    # Rule 4: Rapid Repeat Loop (< 15 seconds since last transaction with high 1h velocity)
    if time_since_prev < 15.0 and txns_1h >= 4:
        triggered_rules.append("RULE_RAPID_REPEAT_LOOP")

    # Rule 5: Severe Odd Hour Anomaly (transacting at polar opposite hour with elevated amount)
    if hour_dev >= 0.8 and cust_avg > 0 and amount > (cust_avg * 1.5):
        triggered_rules.append("RULE_ODD_HOUR_ELEVATED_AMOUNT")

    is_anomaly = 1 if len(triggered_rules) > 0 else 0
    return is_anomaly, triggered_rules


def evaluate_baseline_rules(
    features_df: pd.DataFrame,
) -> np.ndarray:
    """Evaluates heuristic rules on a batch dataframe of features.

    Args:
        features_df: DataFrame containing the model feature columns.

    Returns:
        np.ndarray: Binary array of shape (N,) where 1 = anomalous, 0 = normal.
    """
    if features_df.empty:
        return np.array([], dtype=int)

    preds = np.zeros(len(features_df), dtype=int)
    for idx, (_, row) in enumerate(features_df.iterrows()):
        is_anom, _ = evaluate_single_rule_record(row)
        preds[idx] = is_anom

    return preds


def get_baseline_rule_breakdown(
    features_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Returns detailed predictions with triggered rule breakdown for auditing."""
    records: List[Dict[str, Any]] = []
    for _, row in features_df.iterrows():
        is_anom, triggered = evaluate_single_rule_record(row)
        records.append(
            {
                "prediction": is_anom,
                "triggered_rules": triggered,
                "rule_count": len(triggered),
            }
        )
    return records
