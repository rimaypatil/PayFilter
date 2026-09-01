"""Unified Risk Scorer for PayFilter.

Orchestrates deterministic rule outcomes and ML anomaly model scores with
Phase 1 AdaptiveThresholdManager into final decision tiers (approve / hold / block).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

# Root proxy import from Phase 1
from threshold_manager import AdaptiveThresholdManager
from backend.app.risk_engine.model import MLModelManager, get_model_manager
from backend.app.schemas import RuleResult


class RiskScorer:
    """Combines rule triggers and adaptive ML thresholding to produce machine-readable decisions."""

    def __init__(
        self,
        threshold_manager: Optional[AdaptiveThresholdManager] = None,
        model_manager: Optional[MLModelManager] = None,
        block_threshold_offset: float = 0.25,
    ):
        self.threshold_manager = threshold_manager or AdaptiveThresholdManager(
            initial_threshold=0.45,
            max_change_rate=0.10,
            min_bound=0.15,
            max_bound=0.85,
        )
        self.model_manager = model_manager or get_model_manager()
        self.block_threshold_offset = block_threshold_offset

    def score_transaction(
        self,
        rule_result: RuleResult,
        features: Dict[str, float],
    ) -> Tuple[Literal["approved", "held", "blocked"], float, Dict[str, Any]]:
        """Determines decision tier, anomaly score, and machine-readable structured explanation.

        Decision Rules:
        - block: A hard rule triggered, OR model score >= block_threshold.
        - hold: A soft rule triggered, OR model score >= hold_threshold (and < block_threshold).
        - approve: No rule triggered, and model score < hold_threshold.

        Returns:
            Tuple[status, risk_score, reason_dict]
        """
        # 1. Evaluate hard rule triggers
        if rule_result.triggered and rule_result.rule_type == "hard":
            risk_score = 1.0
            reason = {
                "decision": "blocked",
                "primary_driver": "rule_violation",
                "rule_name": rule_result.rule_name,
                "rule_type": "hard",
                "rule_reason": rule_result.reason,
                "model_score": None,
                "thresholds": {
                    "hold": self.threshold_manager.threshold,
                    "block": min(0.95, self.threshold_manager.threshold + self.block_threshold_offset),
                },
                "feature_drivers": [],
            }
            return "blocked", risk_score, reason

        # 2. Evaluate soft rule triggers
        if rule_result.triggered and rule_result.rule_type == "soft":
            risk_score = 0.65
            reason = {
                "decision": "held",
                "primary_driver": "soft_rule_violation",
                "rule_name": rule_result.rule_name,
                "rule_type": "soft",
                "rule_reason": rule_result.reason,
                "model_score": None,
                "thresholds": {
                    "hold": self.threshold_manager.threshold,
                    "block": min(0.95, self.threshold_manager.threshold + self.block_threshold_offset),
                },
                "feature_drivers": [],
            }
            return "held", risk_score, reason

        # 3. Compute ML model score
        model_score = self.model_manager.score_features(features)
        feature_drivers = self.model_manager.identify_feature_drivers(features)

        hold_threshold = round(self.threshold_manager.threshold, 4)
        block_threshold = round(min(0.95, hold_threshold + self.block_threshold_offset), 4)

        if model_score >= block_threshold:
            status: Literal["approved", "held", "blocked"] = "blocked"
            primary_driver = "high_anomaly_score"
        elif model_score >= hold_threshold:
            status = "held"
            primary_driver = "medium_anomaly_score"
        else:
            status = "approved"
            primary_driver = "normal_baseline"

        reason = {
            "decision": status,
            "primary_driver": primary_driver,
            "rule_name": None,
            "rule_type": None,
            "rule_reason": None,
            "model_score": model_score,
            "thresholds": {
                "hold": hold_threshold,
                "block": block_threshold,
            },
            "feature_drivers": feature_drivers,
        }

        return status, model_score, reason
