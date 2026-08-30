"""Unit tests for baseline heuristic rules in PayFilter."""

import pandas as pd
import pytest

from ml.baseline_rules import (
    evaluate_baseline_rules,
    evaluate_single_rule_record,
    get_baseline_rule_breakdown,
)


def test_normal_transaction_triggers_no_rules():
    """Verify that a normal, typical transaction does not trigger any baseline rules."""
    normal_features = {
        "amount": 500.0,
        "customer_average_amount": 480.0,
        "amount_vs_average_ratio": 1.04,
        "transactions_last_hour": 1.0,
        "transactions_last_day": 3.0,
        "time_since_previous_transaction": 1200.0,
        "merchant_category_frequency": 0.8,
        "agent_type_frequency": 0.9,
        "is_new_merchant_category_for_customer": 0.0,
        "hour_of_day_deviation": 0.0,
    }

    pred, triggered = evaluate_single_rule_record(normal_features)
    assert pred == 0
    assert len(triggered) == 0


def test_extreme_amount_spike_rule_triggers():
    """Verify Rule 1 triggers when amount > 8x customer average."""
    spike_features = {
        "amount": 9000.0,
        "customer_average_amount": 1000.0,  # 9x
        "amount_vs_average_ratio": 9.0,
        "transactions_last_hour": 1.0,
        "transactions_last_day": 2.0,
        "time_since_previous_transaction": 3600.0,
        "merchant_category_frequency": 0.5,
        "agent_type_frequency": 0.5,
        "is_new_merchant_category_for_customer": 0.0,
        "hour_of_day_deviation": 0.0,
    }

    pred, triggered = evaluate_single_rule_record(spike_features)
    assert pred == 1
    assert "RULE_AMOUNT_SPIKE_8X" in triggered


def test_velocity_spike_rule_triggers():
    """Verify Rule 2 triggers when transactions_last_hour > 5."""
    velocity_features = {
        "amount": 300.0,
        "customer_average_amount": 300.0,
        "amount_vs_average_ratio": 1.0,
        "transactions_last_hour": 8.0,
        "transactions_last_day": 10.0,
        "time_since_previous_transaction": 60.0,
        "merchant_category_frequency": 0.5,
        "agent_type_frequency": 0.5,
        "is_new_merchant_category_for_customer": 0.0,
        "hour_of_day_deviation": 0.0,
    }

    pred, triggered = evaluate_single_rule_record(velocity_features)
    assert pred == 1
    assert "RULE_VELOCITY_SPIKE_1H" in triggered


def test_merchant_shift_rule_triggers():
    """Verify Rule 3 triggers on unseen category with amount > 3x average."""
    shift_features = {
        "amount": 4000.0,
        "customer_average_amount": 1000.0,  # 4x
        "amount_vs_average_ratio": 4.0,
        "transactions_last_hour": 1.0,
        "transactions_last_day": 1.0,
        "time_since_previous_transaction": 7200.0,
        "merchant_category_frequency": 0.0,
        "agent_type_frequency": 0.5,
        "is_new_merchant_category_for_customer": 1.0,
        "hour_of_day_deviation": 0.0,
    }

    pred, triggered = evaluate_single_rule_record(shift_features)
    assert pred == 1
    assert "RULE_NEW_MERCHANT_CATEGORY_HIGH_AMOUNT" in triggered


def test_repeat_loop_rule_triggers():
    """Verify Rule 4 triggers on very short intervals with elevated velocity."""
    loop_features = {
        "amount": 500.0,
        "customer_average_amount": 500.0,
        "amount_vs_average_ratio": 1.0,
        "transactions_last_hour": 5.0,
        "transactions_last_day": 5.0,
        "time_since_previous_transaction": 5.0,  # 5s
        "merchant_category_frequency": 1.0,
        "agent_type_frequency": 1.0,
        "is_new_merchant_category_for_customer": 0.0,
        "hour_of_day_deviation": 0.0,
    }

    pred, triggered = evaluate_single_rule_record(loop_features)
    assert pred == 1
    assert "RULE_RAPID_REPEAT_LOOP" in triggered


def test_batch_baseline_rule_evaluation():
    """Verify evaluate_baseline_rules accurately returns numpy array matching individual records."""
    df = pd.DataFrame(
        [
            {
                "amount": 100.0,
                "customer_average_amount": 100.0,
                "transactions_last_hour": 1.0,
                "is_new_merchant_category_for_customer": 0.0,
                "time_since_previous_transaction": 500.0,
                "hour_of_day_deviation": 0.0,
            },
            {
                "amount": 2000.0,
                "customer_average_amount": 100.0,  # 20x spike
                "transactions_last_hour": 1.0,
                "is_new_merchant_category_for_customer": 0.0,
                "time_since_previous_transaction": 500.0,
                "hour_of_day_deviation": 0.0,
            },
        ]
    )

    preds = evaluate_baseline_rules(df)
    assert len(preds) == 2
    assert preds[0] == 0
    assert preds[1] == 1
