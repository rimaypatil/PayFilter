"""Deterministic baseline risk rules engine for PayFilter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from backend.app.db.models import RulesConfig
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.schemas import RuleResult, TransactionCheckRequest


class RuleEngine:
    """Evaluates deterministic merchant policies before ML scoring."""

    def __init__(self, transactions_repo: Optional[TransactionsRepository] = None):
        self.transactions_repo = transactions_repo or TransactionsRepository()

    def evaluate_rules(
        self,
        request: TransactionCheckRequest,
        rules_config: RulesConfig,
    ) -> RuleResult:
        """Evaluates transaction against merchant-configured deterministic rules.

        Rules:
        1. Max amount per order (Hard block)
        2. Category-specific amount limits (Hard block)
        3. Velocity spike: Transactions per minute threshold (Hard block)

        Args:
            request: The incoming transaction payload.
            rules_config: The merchant's configured thresholds.

        Returns:
            RuleResult: Structured outcome detailing if and why a rule fired.
        """
        # 1. Hard cap on max order amount
        if request.amount > rules_config.max_amount_per_order:
            return RuleResult(
                triggered=True,
                rule_name="max_amount_exceeded",
                reason=(
                    f"Transaction amount {request.amount:.2f} exceeds merchant maximum "
                    f"order limit of {rules_config.max_amount_per_order:.2f}"
                ),
                rule_type="hard",
            )

        # 2. Category-specific spending limit
        if rules_config.category_limits:
            cat_limit = rules_config.category_limits.get(request.merchant_category)
            if cat_limit is not None and request.amount > cat_limit:
                return RuleResult(
                    triggered=True,
                    rule_name="category_limit_exceeded",
                    reason=(
                        f"Transaction amount {request.amount:.2f} exceeds limit of {cat_limit:.2f} "
                        f"for merchant category '{request.merchant_category}'"
                    ),
                    rule_type="hard",
                )

        # 3. Velocity check (transactions per minute)
        if rules_config.max_transactions_per_minute > 0:
            one_minute_ago = request.timestamp - timedelta(minutes=1)
            recent_count = self.transactions_repo.get_recent_transactions_count(
                merchant_id=request.merchant_id,
                since_timestamp=one_minute_ago,
            )
            # Including the incoming transaction
            if recent_count >= rules_config.max_transactions_per_minute:
                return RuleResult(
                    triggered=True,
                    rule_name="velocity_limit_exceeded",
                    reason=(
                        f"Merchant transaction velocity ({recent_count + 1}/min) exceeds "
                        f"allowed threshold of {rules_config.max_transactions_per_minute}/min"
                    ),
                    rule_type="hard",
                )

        return RuleResult(triggered=False, rule_name=None, reason=None, rule_type=None)
