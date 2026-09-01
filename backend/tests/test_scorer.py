"""Unit tests for unified risk scorer and decision tiers."""

from typing import Dict
import pytest

from threshold_manager import AdaptiveThresholdManager
from backend.app.risk_engine.scorer import RiskScorer
from backend.app.schemas import RuleResult


class MockMLModelManager:
    """Mock ML manager allowing deterministic anomaly scores for scorer testing."""

    def __init__(self, fixed_score: float = 0.20):
        self.fixed_score = fixed_score

    def score_features(self, features: Dict[str, float]) -> float:
        return self.fixed_score

    def identify_feature_drivers(self, features: Dict[str, float]) -> list:
        if self.fixed_score > 0.5:
            return ["amount_vs_average_ratio (5.0x normal)"]
        return []


def test_scorer_approve_decision():
    """Verify clean transaction with low model score is approved."""
    thresholds = AdaptiveThresholdManager(initial_threshold=0.45)
    model_mock = MockMLModelManager(fixed_score=0.15)
    scorer = RiskScorer(threshold_manager=thresholds, model_manager=model_mock)

    rule_res = RuleResult(triggered=False)
    features = {"amount": 100.0, "amount_vs_average_ratio": 1.0}

    status, score, reason = scorer.score_transaction(rule_res, features)

    assert status == "approved"
    assert score == 0.15
    assert reason["decision"] == "approved"
    assert reason["primary_driver"] == "normal_baseline"
    assert reason["rule_name"] is None
    assert reason["thresholds"]["hold"] == 0.45


def test_scorer_hold_decision_from_medium_score():
    """Verify medium-risk score in [hold_threshold, block_threshold) results in hold."""
    thresholds = AdaptiveThresholdManager(initial_threshold=0.45)
    # 0.55 is >= hold (0.45) but < block (0.45 + 0.25 = 0.70)
    model_mock = MockMLModelManager(fixed_score=0.55)
    scorer = RiskScorer(threshold_manager=thresholds, model_manager=model_mock)

    rule_res = RuleResult(triggered=False)
    features = {"amount": 1200.0, "amount_vs_average_ratio": 3.5}

    status, score, reason = scorer.score_transaction(rule_res, features)

    assert status == "held"
    assert score == 0.55
    assert reason["decision"] == "held"
    assert reason["primary_driver"] == "medium_anomaly_score"
    assert len(reason["feature_drivers"]) > 0


def test_scorer_block_decision_from_high_score():
    """Verify high-risk score >= block_threshold results in block."""
    thresholds = AdaptiveThresholdManager(initial_threshold=0.45)
    # 0.85 is >= block threshold (0.70)
    model_mock = MockMLModelManager(fixed_score=0.85)
    scorer = RiskScorer(threshold_manager=thresholds, model_manager=model_mock)

    rule_res = RuleResult(triggered=False)
    features = {"amount": 50000.0}

    status, score, reason = scorer.score_transaction(rule_res, features)

    assert status == "blocked"
    assert score == 0.85
    assert reason["decision"] == "blocked"
    assert reason["primary_driver"] == "high_anomaly_score"


def test_scorer_block_decision_from_hard_rule():
    """Verify hard rule trigger takes precedence and blocks immediately."""
    thresholds = AdaptiveThresholdManager(initial_threshold=0.45)
    model_mock = MockMLModelManager(fixed_score=0.10)  # low ML score
    scorer = RiskScorer(threshold_manager=thresholds, model_manager=model_mock)

    rule_res = RuleResult(
        triggered=True,
        rule_name="max_amount_exceeded",
        reason="Exceeded limit",
        rule_type="hard",
    )
    features = {"amount": 100000.0}

    status, score, reason = scorer.score_transaction(rule_res, features)

    assert status == "blocked"
    assert score == 1.0
    assert reason["decision"] == "blocked"
    assert reason["primary_driver"] == "rule_violation"
    assert reason["rule_name"] == "max_amount_exceeded"
