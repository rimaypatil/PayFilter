"""Unit tests for adaptive threshold poisoning defense in PayFilter."""

from pathlib import Path
import pytest

from ml.threshold_manager import (
    AdaptiveThresholdManager,
    ThresholdPoisoningError,
)


def test_initial_state():
    """Verify threshold manager initializes with expected defaults and bounds."""
    mgr = AdaptiveThresholdManager(initial_threshold=0.50, max_change_rate=0.10)
    assert mgr.threshold == 0.50
    assert mgr.is_anomaly(0.51) is True
    assert mgr.is_anomaly(0.49) is False


def test_single_update_cap_enforcement():
    """Verify that a massive surge in approvals cannot shift threshold by more than 10% in a single update."""
    mgr = AdaptiveThresholdManager(initial_threshold=0.50, max_change_rate=0.10)

    # Attempt a massive approval wave (10,000 approvals vs 0 denials)
    new_t = mgr.update_from_feedback(approved_count=10000, denied_count=0)

    # Max allowed change is 0.50 * 0.10 = 0.05 -> maximum new threshold = 0.55
    max_allowed = 0.50 * 1.10
    assert new_t <= max_allowed + 1e-5, f"Threshold jumped to {new_t}, exceeding 10% cap!"
    assert new_t > 0.50


def test_adversarial_poisoning_attack_simulation():
    """Adversarial Simulation: Flooding updates with malicious target attempts to force a sudden leap to 0.90."""
    mgr = AdaptiveThresholdManager(initial_threshold=0.50, max_change_rate=0.10)

    # Attacker attempts to jump threshold directly from 0.50 to 0.90 in a single update
    updated_t = mgr.apply_raw_target_update(0.90)

    # Under 10% cap, maximum allowed shift from 0.50 is 0.55
    assert updated_t == pytest.approx(0.55, abs=1e-5)
    assert updated_t < 0.90, "Adversarial target was not constrained by max change rate cap!"

    # If attacker tries again, next jump from 0.55 is at most 0.55 * 1.10 = 0.605
    second_updated_t = mgr.apply_raw_target_update(0.90)
    assert second_updated_t == pytest.approx(0.605, abs=1e-5)


def test_denial_feedback_tightens_threshold():
    """Verify that confirmed fraud / denial feedback shifts threshold downward (tightens risk layer)."""
    mgr = AdaptiveThresholdManager(initial_threshold=0.50, max_change_rate=0.10)

    new_t = mgr.update_from_feedback(approved_count=0, denied_count=1000)
    assert new_t < 0.50
    # Must not drop by more than 10% in one update (minimum = 0.45)
    assert new_t >= 0.45 - 1e-5


def test_state_persistence(tmp_path):
    """Verify state serialization and deserialization retains accurate bounds and history."""
    mgr = AdaptiveThresholdManager(initial_threshold=0.50, max_change_rate=0.10)
    mgr.update_from_feedback(approved_count=50, denied_count=10)

    state_file = tmp_path / "threshold_state.json"
    mgr.save_state(state_file)

    loaded_mgr = AdaptiveThresholdManager.load_state(state_file)
    assert loaded_mgr.threshold == mgr.threshold
    assert loaded_mgr.total_approved == 50
    assert loaded_mgr.total_denied == 10
    assert loaded_mgr.total_updates == 1
