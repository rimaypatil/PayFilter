"""Unit tests for deterministic risk rules."""

from datetime import datetime, timezone
import pytest

from backend.app.db.models import RulesConfig
from backend.app.risk_engine.rules import RuleEngine
from backend.app.schemas import TransactionCheckRequest


class MockTransactionsRepo:
    """Mock repository for transaction velocity testing."""

    def __init__(self, recent_count: int = 0):
        self.recent_count = recent_count

    def get_recent_transactions_count(self, merchant_id: str, since_timestamp: datetime) -> int:
        return self.recent_count


def test_normal_transaction_passes_rules():
    """Verify standard transaction within limits does not trigger any rules."""
    engine = RuleEngine(transactions_repo=MockTransactionsRepo(recent_count=0))
    config = RulesConfig(
        merchant_id="m1",
        max_amount_per_order=10000.0,
        max_transactions_per_minute=5,
        category_limits={"electronics": 15000.0},
    )

    req = TransactionCheckRequest(
        transaction_id="00000000-0000-0000-0000-000000000001",
        merchant_id="m1",
        customer_id="cust_1",
        amount=500.0,
        timestamp=datetime.now(timezone.utc),
        merchant_category="electronics",
        agent_type="procurement_agent",
    )

    res = engine.evaluate_rules(req, config)
    assert res.triggered is False
    assert res.rule_name is None
    assert res.rule_type is None


def test_max_amount_exceeded_rule():
    """Verify transaction exceeding max_amount_per_order triggers hard block rule."""
    engine = RuleEngine(transactions_repo=MockTransactionsRepo(recent_count=0))
    config = RulesConfig(
        merchant_id="m1",
        max_amount_per_order=5000.0,
        max_transactions_per_minute=10,
    )

    req = TransactionCheckRequest(
        transaction_id="00000000-0000-0000-0000-000000000002",
        merchant_id="m1",
        customer_id="cust_1",
        amount=7500.0,
        timestamp=datetime.now(timezone.utc),
        merchant_category="saas",
        agent_type="procurement_agent",
    )

    res = engine.evaluate_rules(req, config)
    assert res.triggered is True
    assert res.rule_name == "max_amount_exceeded"
    assert res.rule_type == "hard"
    assert "exceeds merchant maximum order limit" in res.reason


def test_category_limit_exceeded_rule():
    """Verify transaction exceeding category limit triggers hard block."""
    engine = RuleEngine(transactions_repo=MockTransactionsRepo(recent_count=0))
    config = RulesConfig(
        merchant_id="m1",
        max_amount_per_order=50000.0,
        max_transactions_per_minute=10,
        category_limits={"gift_cards": 2000.0},
    )

    req = TransactionCheckRequest(
        transaction_id="00000000-0000-0000-0000-000000000003",
        merchant_id="m1",
        customer_id="cust_1",
        amount=3500.0,
        timestamp=datetime.now(timezone.utc),
        merchant_category="gift_cards",
        agent_type="procurement_agent",
    )

    res = engine.evaluate_rules(req, config)
    assert res.triggered is True
    assert res.rule_name == "category_limit_exceeded"
    assert res.rule_type == "hard"
    assert "gift_cards" in res.reason


def test_velocity_limit_exceeded_rule():
    """Verify velocity check triggers when recent transactions hit threshold."""
    # 5 prior transactions in the minute, limit is 5
    engine = RuleEngine(transactions_repo=MockTransactionsRepo(recent_count=5))
    config = RulesConfig(
        merchant_id="m1",
        max_amount_per_order=50000.0,
        max_transactions_per_minute=5,
    )

    req = TransactionCheckRequest(
        transaction_id="00000000-0000-0000-0000-000000000004",
        merchant_id="m1",
        customer_id="cust_1",
        amount=100.0,
        timestamp=datetime.now(timezone.utc),
        merchant_category="ecommerce",
        agent_type="procurement_agent",
    )

    res = engine.evaluate_rules(req, config)
    assert res.triggered is True
    assert res.rule_name == "velocity_limit_exceeded"
    assert res.rule_type == "hard"
    assert "velocity" in res.reason
