"""Adaptive Threshold Manager with Poisoning Attack Protection for PayFilter.

Protects anomaly detection decision thresholds against adversarial poisoning attacks.
Ensures thresholds adapt slowly from verified human analyst feedback (approvals/denials),
strictly bounding the maximum allowable delta per update cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ThresholdPoisoningError(Exception):
    """Raised when an update violates safety policies or bounds."""
    pass


@dataclass
class ThresholdState:
    """Serializable state of the adaptive threshold manager."""

    current_threshold: float
    base_threshold: float
    max_change_rate: float
    min_threshold_bound: float
    max_threshold_bound: float
    total_updates: int
    total_approved_signals: int
    total_denied_signals: int


class AdaptiveThresholdManager:
    """Manages adaptive risk scoring thresholds with rate-limiting and drift bounds.

    Attributes:
        initial_threshold: Starting decision threshold (e.g., 0.50).
        max_change_rate: Maximum proportional shift allowed per update cycle (e.g., 0.10 = 10%).
        min_bound: Absolute minimum allowable threshold floor.
        max_bound: Absolute maximum allowable threshold ceiling.
        learning_rate: Sensitivity multiplier for approved vs denied signals.
    """

    def __init__(
        self,
        initial_threshold: float = 0.50,
        max_change_rate: float = 0.10,
        min_bound: float = 0.15,
        max_bound: float = 0.85,
        learning_rate: float = 0.05,
    ) -> None:
        if not (0.0 < initial_threshold < 1.0):
            raise ValueError("initial_threshold must be between 0.0 and 1.0")
        if not (0.0 < max_change_rate <= 0.50):
            raise ValueError("max_change_rate must be between 0.0 and 0.50")
        if min_bound >= max_bound:
            raise ValueError("min_bound must be strictly less than max_bound")

        self.base_threshold: float = float(initial_threshold)
        self.current_threshold: float = float(initial_threshold)
        self.max_change_rate: float = float(max_change_rate)
        self.min_bound: float = float(min_bound)
        self.max_bound: float = float(max_bound)
        self.learning_rate: float = float(learning_rate)

        self.total_updates: int = 0
        self.total_approved: int = 0
        self.total_denied: int = 0

    @property
    def threshold(self) -> float:
        """Returns the current effective threshold."""
        return self.current_threshold

    def is_anomaly(self, score: float) -> bool:
        """Determines if a given risk/anomaly score exceeds the threshold.

        Higher score indicates higher anomaly confidence.
        """
        return score >= self.current_threshold

    def update_from_feedback(
        self,
        approved_count: int,
        denied_count: int,
    ) -> float:
        """Updates threshold based on human review feedback on held transactions.

        - More approvals on held transactions indicate false positives: threshold should ease up (increase).
        - More denials on held transactions indicate true attacks: threshold should tighten (decrease).

        The resulting delta is strictly clamped to max_change_rate * current_threshold.

        Args:
            approved_count: Number of human-approved held transactions.
            denied_count: Number of human-denied/confirmed-fraud held transactions.

        Returns:
            float: The newly updated, bounded threshold.
        """
        total = approved_count + denied_count
        if total == 0:
            return self.current_threshold

        self.total_approved += approved_count
        self.total_denied += denied_count
        self.total_updates += 1

        # Net signal ratio: +1 if 100% approved, -1 if 100% denied
        net_signal = (approved_count - denied_count) / float(total)

        # Unconstrained candidate delta
        raw_delta = net_signal * self.learning_rate * self.current_threshold

        # Enforce maximum change rate cap
        max_allowed_delta = self.current_threshold * self.max_change_rate
        clamped_delta = max(-max_allowed_delta, min(max_allowed_delta, raw_delta))

        new_threshold = self.current_threshold + clamped_delta

        # Enforce absolute safety bounds
        new_threshold = max(self.min_bound, min(self.max_bound, new_threshold))
        self.current_threshold = round(new_threshold, 6)

        return self.current_threshold

    def update_threshold(self, is_fraud: bool) -> float:
        """Convenience method to feed a single human confirmation decision."""
        if is_fraud:
            return self.update_from_feedback(approved_count=0, denied_count=1)
        else:
            return self.update_from_feedback(approved_count=1, denied_count=0)

    def apply_raw_target_update(self, proposed_target: float) -> float:
        """Applies a proposed target threshold while strictly enforcing maximum delta caps.

        Simulates an external optimizer or adversarial prompt attempting to jump the threshold.

        Args:
            proposed_target: The desired new threshold.

        Returns:
            float: The actual applied threshold after strict cap enforcement.
        """
        raw_delta = proposed_target - self.current_threshold
        max_allowed_delta = self.current_threshold * self.max_change_rate
        clamped_delta = max(-max_allowed_delta, min(max_allowed_delta, raw_delta))

        new_threshold = self.current_threshold + clamped_delta
        new_threshold = max(self.min_bound, min(self.max_bound, new_threshold))
        self.current_threshold = round(new_threshold, 6)
        self.total_updates += 1
        return self.current_threshold

    def get_state(self) -> ThresholdState:
        """Returns the current state representation."""
        return ThresholdState(
            current_threshold=self.current_threshold,
            base_threshold=self.base_threshold,
            max_change_rate=self.max_change_rate,
            min_threshold_bound=self.min_bound,
            max_threshold_bound=self.max_bound,
            total_updates=self.total_updates,
            total_approved_signals=self.total_approved,
            total_denied_signals=self.total_denied,
        )

    def save_state(self, file_path: Union[str, Path]) -> None:
        """Serializes manager state to a JSON file."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(asdict(self.get_state()), f, indent=2)

    @classmethod
    def load_state(cls, file_path: Union[str, Path]) -> AdaptiveThresholdManager:
        """Loads state from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        mgr = cls(
            initial_threshold=data["current_threshold"],
            max_change_rate=data["max_change_rate"],
            min_bound=data["min_threshold_bound"],
            max_bound=data["max_threshold_bound"],
        )
        mgr.base_threshold = data["base_threshold"]
        mgr.total_updates = data["total_updates"]
        mgr.total_approved = data["total_approved_signals"]
        mgr.total_denied = data["total_denied_signals"]
        return mgr
