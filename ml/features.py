"""Feature Engineering Module for PayFilter.

Transforms raw transaction records into leakage-safe numerical feature representations
suitable for real-time anomaly detection models and baseline heuristics.

CRITICAL LEAKAGE PREVENTION:
All rolling/historical features (customer averages, transaction velocity counts, category frequencies,
and hour deviations) are strictly computed over historical transactions that occurred *strictly before*
the current transaction's timestamp (t_hist < t_current).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

FEATURE_COLUMNS: List[str] = [
    "amount",
    "customer_average_amount",
    "amount_vs_average_ratio",
    "transactions_last_hour",
    "transactions_last_day",
    "time_since_previous_transaction",
    "merchant_category_frequency",
    "agent_type_frequency",
    "is_new_merchant_category_for_customer",
    "hour_of_day_deviation",
]

DEFAULT_FALLBACK_AMOUNT: float = 1000.0
DEFAULT_FALLBACK_TIME_DELTA: float = 86400.0  # 24 hours in seconds


def _circular_hour_distance(h1: int, h2: int) -> float:
    """Computes circular distance between two hours on a 24-hour clock (0 to 12)."""
    diff = abs(h1 - h2)
    return min(diff, 24 - diff)


def _compute_hour_deviation(current_hour: int, past_hours: List[int]) -> float:
    """Computes normalized deviation of current hour relative to customer's historical hours.

    Returns:
        float: 0.0 (exact match with past hour) to 1.0 (opposite time of day, 12h away).
               Returns 0.0 (neutral) if no history is available.
    """
    if not past_hours:
        return 0.0
    min_dist = min(_circular_hour_distance(current_hour, ph) for ph in past_hours)
    return float(min_dist / 12.0)


def extract_features(
    df: pd.DataFrame,
    global_avg_amount_fallback: Optional[float] = None,
) -> pd.DataFrame:
    """Extracts leakage-safe feature vectors from a batch transaction dataframe.

    Processes records chronologically to ensure strict temporal separation. No future
    information relative to transaction timestamp t is ever accessed.

    Args:
        df: Input DataFrame containing raw transactions:
            - transaction_id
            - customer_id
            - merchant_id
            - amount
            - timestamp
            - merchant_category
            - agent_type
        global_avg_amount_fallback: Fallback amount for customers with no prior history.
            If None, defaults to the overall mean amount of the dataset.

    Returns:
        pd.DataFrame: Feature matrix containing exact FEATURE_COLUMNS, with zero NaNs.
    """
    if df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS, dtype=float)

    # Ensure timestamp is datetime and sort chronologically
    df_sorted = df.copy()
    df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
    df_sorted = df_sorted.sort_values(by="timestamp").reset_index()
    original_indices = df_sorted["index"].values

    if global_avg_amount_fallback is None:
        global_avg = float(df_sorted["amount"].mean()) if not df_sorted.empty else DEFAULT_FALLBACK_AMOUNT
    else:
        global_avg = float(global_avg_amount_fallback)

    n = len(df_sorted)
    # Feature arrays
    f_amount = df_sorted["amount"].astype(float).values
    f_cust_avg = np.zeros(n, dtype=float)
    f_amt_ratio = np.zeros(n, dtype=float)
    f_txns_1h = np.zeros(n, dtype=float)
    f_txns_1d = np.zeros(n, dtype=float)
    f_time_since_prev = np.zeros(n, dtype=float)
    f_cat_freq = np.zeros(n, dtype=float)
    f_agent_freq = np.zeros(n, dtype=float)
    f_is_new_cat = np.zeros(n, dtype=float)
    f_hour_dev = np.zeros(n, dtype=float)

    # Track per-customer historical state
    # customer_id -> dict of past records
    cust_history: Dict[str, Dict[str, Any]] = {}

    for i in range(n):
        cust_id = df_sorted.at[i, "customer_id"]
        amt = float(df_sorted.at[i, "amount"])
        t_curr = df_sorted.at[i, "timestamp"]
        cat = str(df_sorted.at[i, "merchant_category"])
        agent = str(df_sorted.at[i, "agent_type"])
        curr_hour = t_curr.hour

        if cust_id not in cust_history:
            # First transaction for this customer (no prior history)
            f_cust_avg[i] = amt  # Fallback to current transaction amount or global_avg
            f_amt_ratio[i] = 1.0  # Safe ratio for baseline
            f_txns_1h[i] = 0.0
            f_txns_1d[i] = 0.0
            f_time_since_prev[i] = DEFAULT_FALLBACK_TIME_DELTA
            f_cat_freq[i] = 0.0
            f_agent_freq[i] = 0.0
            f_is_new_cat[i] = 1.0
            f_hour_dev[i] = 0.0

            # Initialize history
            cust_history[cust_id] = {
                "amounts": [amt],
                "timestamps": [t_curr],
                "categories": {cat: 1},
                "agent_types": {agent: 1},
                "hours": [curr_hour],
            }
        else:
            hist = cust_history[cust_id]
            past_amounts: List[float] = hist["amounts"]
            past_timestamps: List[datetime] = hist["timestamps"]
            past_cats: Dict[str, int] = hist["categories"]
            past_agents: Dict[str, int] = hist["agent_types"]
            past_hours: List[int] = hist["hours"]

            # 1. Customer historical average amount (strictly prior)
            prior_avg = float(np.mean(past_amounts))
            f_cust_avg[i] = prior_avg
            f_amt_ratio[i] = float(amt / prior_avg) if prior_avg > 0 else 1.0

            # 2. Time windows: 1 hour and 24 hours strictly before t_curr
            one_hour_ago = t_curr - timedelta(hours=1)
            one_day_ago = t_curr - timedelta(days=1)

            # Count past timestamps in windows
            count_1h = sum(1 for pt in past_timestamps if pt >= one_hour_ago)
            count_1d = sum(1 for pt in past_timestamps if pt >= one_day_ago)
            f_txns_1h[i] = float(count_1h)
            f_txns_1d[i] = float(count_1d)

            # 3. Time since previous transaction
            prev_t = past_timestamps[-1]
            elapsed_sec = max(0.0, (t_curr - prev_t).total_seconds())
            f_time_since_prev[i] = float(elapsed_sec)

            # 4. Frequencies
            total_past = len(past_amounts)
            cat_count = past_cats.get(cat, 0)
            agent_count = past_agents.get(agent, 0)

            f_cat_freq[i] = float(cat_count / total_past)
            f_agent_freq[i] = float(agent_count / total_past)
            f_is_new_cat[i] = 1.0 if cat_count == 0 else 0.0

            # 5. Hour deviation relative to customer's own diurnal distribution
            f_hour_dev[i] = _compute_hour_deviation(curr_hour, past_hours)

            # Update history with current transaction
            past_amounts.append(amt)
            past_timestamps.append(t_curr)
            past_cats[cat] = cat_count + 1
            past_agents[agent] = agent_count + 1
            past_hours.append(curr_hour)

    features_df = pd.DataFrame(
        {
            "amount": f_amount,
            "customer_average_amount": f_cust_avg,
            "amount_vs_average_ratio": f_amt_ratio,
            "transactions_last_hour": f_txns_1h,
            "transactions_last_day": f_txns_1d,
            "time_since_previous_transaction": f_time_since_prev,
            "merchant_category_frequency": f_cat_freq,
            "agent_type_frequency": f_agent_freq,
            "is_new_merchant_category_for_customer": f_is_new_cat,
            "hour_of_day_deviation": f_hour_dev,
        },
        index=original_indices,
    )

    # Reorder back to original dataframe order
    features_df = features_df.sort_index()

    # Safety check: replace any possible infinite or NaN values
    features_df = features_df.fillna(0.0)
    features_df = features_df.replace([np.inf, -np.inf], 0.0)

    return features_df[FEATURE_COLUMNS]


def extract_single_transaction_features(
    current_txn: Union[Dict[str, Any], pd.Series],
    customer_history_df: Optional[pd.DataFrame] = None,
    global_avg_amount_fallback: float = DEFAULT_FALLBACK_AMOUNT,
) -> Dict[str, float]:
    """Extracts features for a single incoming transaction during online scoring.

    Designed for Phase 2 backend ingestion. Evaluates strictly against confirmed
    past customer transaction history.

    Args:
        current_txn: Dictionary or Series with transaction keys:
            - customer_id, amount, timestamp, merchant_category, agent_type
        customer_history_df: DataFrame of prior transactions for this customer (t_past < t_curr).
        global_avg_amount_fallback: Fallback baseline if customer has no history.

    Returns:
        Dict[str, float]: Feature dictionary keyed by FEATURE_COLUMNS.
    """
    amt = float(current_txn["amount"])
    t_curr = pd.to_datetime(current_txn["timestamp"])
    cat = str(current_txn["merchant_category"])
    agent = str(current_txn.get("agent_type", "unknown"))
    curr_hour = t_curr.hour

    if customer_history_df is None or customer_history_df.empty:
        return {
            "amount": amt,
            "customer_average_amount": amt if amt > 0 else global_avg_amount_fallback,
            "amount_vs_average_ratio": 1.0,
            "transactions_last_hour": 0.0,
            "transactions_last_day": 0.0,
            "time_since_previous_transaction": DEFAULT_FALLBACK_TIME_DELTA,
            "merchant_category_frequency": 0.0,
            "agent_type_frequency": 0.0,
            "is_new_merchant_category_for_customer": 1.0,
            "hour_of_day_deviation": 0.0,
        }

    # Filter history to strictly prior timestamps
    hist = customer_history_df.copy()
    hist["timestamp"] = pd.to_datetime(hist["timestamp"])
    prior_txns = hist[hist["timestamp"] < t_curr].sort_values(by="timestamp")

    if prior_txns.empty:
        return {
            "amount": amt,
            "customer_average_amount": amt if amt > 0 else global_avg_amount_fallback,
            "amount_vs_average_ratio": 1.0,
            "transactions_last_hour": 0.0,
            "transactions_last_day": 0.0,
            "time_since_previous_transaction": DEFAULT_FALLBACK_TIME_DELTA,
            "merchant_category_frequency": 0.0,
            "agent_type_frequency": 0.0,
            "is_new_merchant_category_for_customer": 1.0,
            "hour_of_day_deviation": 0.0,
        }

    prior_amounts = prior_txns["amount"].astype(float).values
    prior_avg = float(np.mean(prior_amounts)) if len(prior_amounts) > 0 else global_avg_amount_fallback
    amt_ratio = float(amt / prior_avg) if prior_avg > 0 else 1.0

    one_hour_ago = t_curr - timedelta(hours=1)
    one_day_ago = t_curr - timedelta(days=1)
    txns_1h = float((prior_txns["timestamp"] >= one_hour_ago).sum())
    txns_1d = float((prior_txns["timestamp"] >= one_day_ago).sum())

    prev_time = prior_txns["timestamp"].iloc[-1]
    time_since_prev = max(0.0, (t_curr - prev_time).total_seconds())

    total_prior = len(prior_txns)
    cat_match_count = (prior_txns["merchant_category"] == cat).sum()
    cat_freq = float(cat_match_count / total_prior)
    is_new_cat = 1.0 if cat_match_count == 0 else 0.0

    if "agent_type" in prior_txns.columns:
        agent_match_count = (prior_txns["agent_type"] == agent).sum()
        agent_freq = float(agent_match_count / total_prior)
    else:
        agent_freq = 0.0

    past_hours = prior_txns["timestamp"].dt.hour.tolist()
    hour_dev = _compute_hour_deviation(curr_hour, past_hours)

    return {
        "amount": amt,
        "customer_average_amount": prior_avg,
        "amount_vs_average_ratio": amt_ratio,
        "transactions_last_hour": txns_1h,
        "transactions_last_day": txns_1d,
        "time_since_previous_transaction": time_since_prev,
        "merchant_category_frequency": cat_freq,
        "agent_type_frequency": agent_freq,
        "is_new_merchant_category_for_customer": is_new_cat,
        "hour_of_day_deviation": hour_dev,
    }
