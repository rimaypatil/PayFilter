"""Synthetic Transaction Generator for PayFilter.

Generates realistic AI-agent-initiated transaction streams with embedded anomaly patterns
including velocity spikes, agent repeat loops, extreme amount spikes, merchant category shifts,
and customer-specific odd-hour bursts.

CRITICAL NOTE ON ANOMALY RATE:
In real-world production environments, fraud and anomaly rates are typically under 1%.
However, for this synthetic benchmark dataset, we intentionally maintain an anomaly rate
of ~4.5% (~450 anomalous transactions out of ~10,450 total transactions). This deliberate
compromise guarantees sufficient statistical support to evaluate distinct anomaly subtypes
and prevent severe class starvation during cross-validation and testing.
When training the IsolationForest model, the contamination parameter is deliberately set
to reflect the assumed real-world rate (e.g. 0.015 / 1.5%), rather than the synthetic
dataset's inflated rate.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import os
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union

# Categories and Agent Types
MERCHANT_CATEGORIES: List[str] = [
    "ecommerce",
    "saas",
    "travel",
    "gaming",
    "utilities",
    "food_delivery",
    "luxury",
    "electronics",
    "crypto",
]

AGENT_TYPES: List[str] = [
    "procurement_agent",
    "customer_service_bot",
    "personal_assistant",
    "automated_scheduler",
    "code_assistant",
    "browser_subagent",
]

BASE_MERCHANTS_PER_CATEGORY: int = 6


@dataclass
class CustomerProfile:
    """Represents a synthetic customer's behavioral baseline."""

    customer_id: str
    base_mean_amount: float
    base_std_amount: float
    preferred_categories: List[str]
    preferred_agent_types: List[str]
    active_hours: List[int]  # Regular operating hours (e.g. 9 to 18)
    daily_frequency_mean: float  # Average txns per day


def build_customer_profiles(
    num_customers: int = 150,
    rng: Optional[random.Random] = None,
) -> List[CustomerProfile]:
    """Constructs realistic customer behavioral profiles with distinctive patterns."""
    if rng is None:
        rng = random.Random(42)

    profiles: List[CustomerProfile] = []

    for i in range(1, num_customers + 1):
        cust_id = f"cust_{i:04d}"

        # Segment customers into spending tiers: micro, standard, high-volume enterprise
        tier = rng.choices(["micro", "standard", "enterprise"], weights=[0.4, 0.45, 0.15])[0]
        if tier == "micro":
            mean_amt = rng.uniform(150.0, 800.0)
            std_amt = mean_amt * rng.uniform(0.15, 0.35)
            freq = rng.uniform(0.5, 2.0)
        elif tier == "standard":
            mean_amt = rng.uniform(800.0, 3500.0)
            std_amt = mean_amt * rng.uniform(0.20, 0.40)
            freq = rng.uniform(1.5, 5.0)
        else:  # enterprise
            mean_amt = rng.uniform(4000.0, 18000.0)
            std_amt = mean_amt * rng.uniform(0.25, 0.50)
            freq = rng.uniform(4.0, 12.0)

        # Assign 2-4 primary merchant categories (normal customers don't transact everywhere)
        num_fav_cats = rng.randint(2, 4)
        fav_cats = rng.sample(MERCHANT_CATEGORIES[:6], k=num_fav_cats)

        # Primary agents used by this customer
        num_fav_agents = rng.randint(1, 3)
        fav_agents = rng.sample(AGENT_TYPES, k=num_fav_agents)

        # Regular business/active hours (e.g. 8 to 20)
        start_hour = rng.randint(7, 10)
        end_hour = rng.randint(18, 22)
        active_hours = list(range(start_hour, end_hour + 1))

        profiles.append(
            CustomerProfile(
                customer_id=cust_id,
                base_mean_amount=round(mean_amt, 2),
                base_std_amount=round(std_amt, 2),
                preferred_categories=fav_cats,
                preferred_agent_types=fav_agents,
                active_hours=active_hours,
                daily_frequency_mean=freq,
            )
        )

    return profiles


def generate_merchants() -> Dict[str, List[str]]:
    """Maps merchant categories to fake merchant IDs."""
    mapping: Dict[str, List[str]] = {}
    merch_counter = 1
    for cat in MERCHANT_CATEGORIES:
        merchants = []
        for _ in range(BASE_MERCHANTS_PER_CATEGORY):
            merchants.append(f"merch_{merch_counter:04d}")
            merch_counter += 1
        mapping[cat] = merchants
    return mapping


def generate_raw_transaction_records(
    target_normal: int = 10000,
    target_anomalous: int = 450,
    num_days: int = 60,
    random_seed: int = 42,
) -> List[Dict[str, Any]]:
    """Generates pure Python dictionaries of normal and anomalous transactions."""
    rng = random.Random(random_seed)

    profiles = build_customer_profiles(num_customers=150, rng=rng)
    merchants_by_cat = generate_merchants()

    start_date = datetime(2026, 1, 1, 0, 0, 0)
    all_transactions: List[Dict[str, Any]] = []

    # 1. Generate Normal Transactions
    for profile in profiles:
        expected_txns = int(profile.daily_frequency_mean * num_days)
        actual_count = max(5, int(rng.gauss(expected_txns, max(1.0, expected_txns * 0.15))))

        for _ in range(actual_count):
            day_offset = rng.uniform(0, num_days - 0.05)
            day_int = int(day_offset)
            hour = rng.choice(profile.active_hours)
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            microsecond = rng.randint(0, 999999)

            txn_time = start_date + timedelta(
                days=day_int,
                hours=hour,
                minutes=minute,
                seconds=second,
                microseconds=microsecond,
            )

            # Amount drawn from customer's normal distribution (truncated positive)
            amt = float(rng.gauss(profile.base_mean_amount, profile.base_std_amount))
            amt = max(10.0, round(amt, 2))

            category = rng.choice(profile.preferred_categories)
            merchant_id = rng.choice(merchants_by_cat[category])
            agent_type = rng.choice(profile.preferred_agent_types)

            all_transactions.append(
                {
                    "customer_id": profile.customer_id,
                    "merchant_id": merchant_id,
                    "amount": amt,
                    "timestamp": txn_time,
                    "merchant_category": category,
                    "agent_type": agent_type,
                    "label": 0,
                    "anomaly_type": "none",
                }
            )

    # Top-up normal transactions to meet target
    while len(all_transactions) < target_normal:
        profile = rng.choice(profiles)
        day_offset = rng.uniform(0, num_days - 0.05)
        day_int = int(day_offset)
        hour = rng.choice(profile.active_hours)
        txn_time = start_date + timedelta(
            days=day_int,
            hours=hour,
            minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59),
            microseconds=rng.randint(0, 999999),
        )
        amt = max(10.0, round(float(rng.gauss(profile.base_mean_amount, profile.base_std_amount)), 2))
        category = rng.choice(profile.preferred_categories)
        all_transactions.append(
            {
                "customer_id": profile.customer_id,
                "merchant_id": rng.choice(merchants_by_cat[category]),
                "amount": amt,
                "timestamp": txn_time,
                "merchant_category": category,
                "agent_type": rng.choice(profile.preferred_agent_types),
                "label": 0,
                "anomaly_type": "none",
            }
        )

    # 2. Generate 5 Distinct Anomaly Types (~90 instances each)
    anomalies_per_type = max(80, target_anomalous // 5)
    anomalous_transactions: List[Dict[str, Any]] = []

    def pick_anomaly_day() -> int:
        return rng.randint(5, num_days - 2)

    # --- Anomaly Type 1: Velocity Spike ---
    for _ in range(anomalies_per_type // 6 + 1):
        profile = rng.choice(profiles)
        day_int = pick_anomaly_day()
        base_hour = rng.choice(profile.active_hours)
        base_minute = rng.randint(0, 40)
        base_time = start_date + timedelta(days=day_int, hours=base_hour, minutes=base_minute)

        burst_size = rng.randint(5, 8)
        for b in range(burst_size):
            offset_seconds = b * rng.randint(30, 90)
            txn_time = base_time + timedelta(seconds=offset_seconds)
            category = rng.choice(MERCHANT_CATEGORIES)
            merch = rng.choice(merchants_by_cat[category])
            amt = round(profile.base_mean_amount * rng.uniform(0.8, 1.8), 2)
            anomalous_transactions.append(
                {
                    "customer_id": profile.customer_id,
                    "merchant_id": merch,
                    "amount": amt,
                    "timestamp": txn_time,
                    "merchant_category": category,
                    "agent_type": rng.choice(AGENT_TYPES),
                    "label": 1,
                    "anomaly_type": "velocity_spike",
                }
            )

    # --- Anomaly Type 2: Repeat Loop ---
    for _ in range(anomalies_per_type // 6 + 1):
        profile = rng.choice(profiles)
        day_int = pick_anomaly_day()
        base_hour = rng.choice(profile.active_hours)
        base_minute = rng.randint(0, 45)
        base_time = start_date + timedelta(days=day_int, hours=base_hour, minutes=base_minute)

        loop_merch_cat = rng.choice(profile.preferred_categories)
        loop_merch = rng.choice(merchants_by_cat[loop_merch_cat])
        loop_amt = round(profile.base_mean_amount * rng.uniform(0.9, 1.2), 2)
        loop_agent = rng.choice(profile.preferred_agent_types)

        loop_size = rng.randint(5, 7)
        for l_idx in range(loop_size):
            offset_seconds = l_idx * rng.randint(3, 12)
            txn_time = base_time + timedelta(seconds=offset_seconds)
            anomalous_transactions.append(
                {
                    "customer_id": profile.customer_id,
                    "merchant_id": loop_merch,
                    "amount": loop_amt,
                    "timestamp": txn_time,
                    "merchant_category": loop_merch_cat,
                    "agent_type": loop_agent,
                    "label": 1,
                    "anomaly_type": "repeat_loop",
                }
            )

    # --- Anomaly Type 3: Amount Spike ---
    for _ in range(anomalies_per_type):
        profile = rng.choice(profiles)
        day_int = pick_anomaly_day()
        hour = rng.choice(profile.active_hours)
        txn_time = start_date + timedelta(
            days=day_int,
            hours=hour,
            minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59),
        )
        spike_multiplier = rng.uniform(10.0, 25.0)
        spike_amt = round(profile.base_mean_amount * spike_multiplier, 2)
        category = rng.choice(profile.preferred_categories)
        anomalous_transactions.append(
            {
                "customer_id": profile.customer_id,
                "merchant_id": rng.choice(merchants_by_cat[category]),
                "amount": spike_amt,
                "timestamp": txn_time,
                "merchant_category": category,
                "agent_type": rng.choice(profile.preferred_agent_types),
                "label": 1,
                "anomaly_type": "amount_spike",
            }
        )

    # --- Anomaly Type 4: Merchant Shift ---
    high_risk_unseen_cats = ["luxury", "crypto", "electronics"]
    for _ in range(anomalies_per_type):
        profile = rng.choice(profiles)
        day_int = pick_anomaly_day()
        hour = rng.choice(profile.active_hours)
        txn_time = start_date + timedelta(
            days=day_int,
            hours=hour,
            minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59),
        )
        unseen_cats = [c for c in MERCHANT_CATEGORIES if c not in profile.preferred_categories]
        shift_cat = rng.choice(unseen_cats if unseen_cats else high_risk_unseen_cats)
        shift_merch = rng.choice(merchants_by_cat[shift_cat])
        shift_amt = round(profile.base_mean_amount * rng.uniform(3.5, 7.5), 2)
        anomalous_transactions.append(
            {
                "customer_id": profile.customer_id,
                "merchant_id": shift_merch,
                "amount": shift_amt,
                "timestamp": txn_time,
                "merchant_category": shift_cat,
                "agent_type": rng.choice(AGENT_TYPES),
                "label": 1,
                "anomaly_type": "merchant_shift",
            }
        )

    # --- Anomaly Type 5: Odd-Hour Burst ---
    for _ in range(anomalies_per_type):
        profile = rng.choice(profiles)
        day_int = pick_anomaly_day()
        odd_hours = [h for h in range(24) if h not in profile.active_hours]
        odd_hour = rng.choice(odd_hours if odd_hours else [2, 3, 4])
        txn_time = start_date + timedelta(
            days=day_int,
            hours=odd_hour,
            minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59),
        )
        category = rng.choice(profile.preferred_categories)
        amt = round(profile.base_mean_amount * rng.uniform(1.2, 3.0), 2)
        anomalous_transactions.append(
            {
                "customer_id": profile.customer_id,
                "merchant_id": rng.choice(merchants_by_cat[category]),
                "amount": amt,
                "timestamp": txn_time,
                "merchant_category": category,
                "agent_type": rng.choice(profile.preferred_agent_types),
                "label": 1,
                "anomaly_type": "odd_hour_burst",
            }
        )

    # Combine and sort strictly chronologically by timestamp
    all_records = all_transactions + anomalous_transactions
    all_records.sort(key=lambda x: x["timestamp"])

    # Assign sequential transaction IDs and ISO timestamps
    for idx, rec in enumerate(all_records, start=1):
        rec["transaction_id"] = f"txn_{idx:06d}"
        rec["timestamp"] = rec["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    return all_records


def generate_synthetic_transactions(
    target_normal: int = 10000,
    target_anomalous: int = 450,
    num_days: int = 60,
    random_seed: int = 42,
) -> Any:
    """Generates synthetic dataset and returns as pandas DataFrame."""
    import pandas as pd  # Lazy import

    records = generate_raw_transaction_records(
        target_normal=target_normal,
        target_anomalous=target_anomalous,
        num_days=num_days,
        random_seed=random_seed,
    )
    df = pd.DataFrame(records)
    cols = [
        "transaction_id",
        "customer_id",
        "merchant_id",
        "amount",
        "timestamp",
        "merchant_category",
        "agent_type",
        "label",
        "anomaly_type",
    ]
    return df[cols]


def save_synthetic_data(
    records_or_df: Any,
    output_path: Optional[str | Path] = None,
) -> Path:
    """Saves generated dataset to CSV."""
    if output_path is None:
        base_dir = Path(__file__).resolve().parent
        output_path = base_dir / "data" / "synthetic_transactions.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "transaction_id",
        "customer_id",
        "merchant_id",
        "amount",
        "timestamp",
        "merchant_category",
        "agent_type",
        "label",
        "anomaly_type",
    ]

    if hasattr(records_or_df, "to_csv"):
        records_or_df.to_csv(output_path, index=False)
        total = len(records_or_df)
        normal = (records_or_df["label"] == 0).sum()
        anom = (records_or_df["label"] == 1).sum()
    else:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records_or_df:
                writer.writerow(r)
        total = len(records_or_df)
        normal = sum(1 for r in records_or_df if r["label"] == 0)
        anom = sum(1 for r in records_or_df if r["label"] == 1)

    print(f"Saved {total} synthetic transactions to {output_path}")
    print(f"Normal: {normal}, Anomalous: {anom} (Anomaly Rate: {anom / total:.4%})")
    return output_path


def main() -> None:
    """CLI entrypoint for data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic transaction data for PayFilter")
    parser.add_argument("--normal", type=int, default=10000, help="Minimum normal transactions")
    parser.add_argument("--anomalous", type=int, default=450, help="Target anomalous transactions")
    parser.add_argument("--days", type=int, default=60, help="Number of days span")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")

    args = parser.parse_args()
    records = generate_raw_transaction_records(
        target_normal=args.normal,
        target_anomalous=args.anomalous,
        num_days=args.days,
        random_seed=args.seed,
    )
    save_synthetic_data(records, args.output)


if __name__ == "__main__":
    main()
