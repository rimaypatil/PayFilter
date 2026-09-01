"""Anthropic Claude Integration for Plain-English Risk Explanations."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.app.config import get_settings

logger = logging.getLogger("payfilter.integrations.claude")


class ClaudeClient:
    """Generates natural language risk explanations for held or blocked transactions."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 5.0):
        settings = get_settings()
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.timeout = timeout or settings.CLAUDE_TIMEOUT_SECONDS

        self._client = None
        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
                logger.info("Initialized Anthropic Claude client for risk explanations.")
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic SDK: {e}. Will use deterministic fallback.")

    def explain_decision(
        self,
        scorer_output: Dict[str, Any],
        amount: Optional[float] = None,
        category: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> str:
        """Translates structured risk engine outputs into 1-2 plain-English sentences.

        Data Minimization Guarantee (MANDATORY):
        Only numerical and categorical features already computed by the risk engine are sent.
        NEVER sends raw customer names, emails, addresses, card details, or sensitive PII.

        Timeout and Failure Tolerance:
        If Claude API times out (5s) or fails, returns a clean fallback string.
        The PayFilter risk decision is NEVER compromised or blocked by an external API outage.

        Args:
            scorer_output: Structured reason dictionary from RiskScorer.
            amount: Transaction order amount in INR.
            category: Merchant business category.
            agent_type: AI agent category.

        Returns:
            str: 1-2 sentence plain-English explanation for risk analysts.
        """
        # 1. Extract sanitized metrics strictly without PII
        decision = scorer_output.get("decision", "held")
        primary_driver = scorer_output.get("primary_driver", "anomaly_score")
        rule_name = scorer_output.get("rule_triggered") or primary_driver
        risk_score = scorer_output.get("risk_score") or scorer_output.get("model_score", 0.5)
        drivers = scorer_output.get("feature_drivers", [])

        # 2. Build sanitized context payload (PII-free)
        sanitized_context = {
            "decision": decision,
            "rule_name": rule_name,
            "risk_score": round(float(risk_score), 4),
            "amount_inr": amount,
            "category": category,
            "agent_type": agent_type,
            "primary_driver": primary_driver,
            "feature_drivers": drivers,
        }

        # 3. Call Claude API if client configured
        if self._client:
            try:
                prompt = (
                    f"You are a payment risk analyst assistant. Write 1 or 2 concise, plain-English sentences "
                    f"explaining why this transaction was marked as '{decision.upper()}' to a human analyst. "
                    f"Be direct, factual, and mention the relevant numbers or rule without jargon.\n\n"
                    f"Risk telemetry: {sanitized_context}"
                )

                response = self._client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    temperature=0.2,
                    system="You are an expert fraud & risk analyst. Output only the 1-2 explanatory sentences.",
                    messages=[{"role": "user", "content": prompt}],
                )

                content_blocks = response.content
                if content_blocks and len(content_blocks) > 0:
                    explanation_text = content_blocks[0].text.strip()
                    logger.info(f"Generated Claude risk explanation: {explanation_text}")
                    return explanation_text

            except Exception as exc:
                logger.warning(
                    f"Claude API explanation call failed or timed out ({self.timeout}s): {exc}. "
                    "Using graceful fallback explanation.",
                )

        # 4. Deterministic Graceful Fallback (Failure-Tolerant)
        return self._generate_fallback_explanation(decision, rule_name, amount, risk_score, primary_driver)

    def _generate_fallback_explanation(
        self,
        decision: str,
        rule_name: str,
        amount: Optional[float],
        risk_score: float,
        primary_driver: str,
    ) -> str:
        """Generates clear, deterministic fallback explanation when Claude API is offline or times out."""
        amt_str = f" of ₹{amount:,.2f}" if amount is not None else ""

        if "velocity" in primary_driver.lower() or "velocity" in rule_name.lower():
            return f"Transaction{amt_str} was flagged due to rapid purchase velocity exceeding typical customer frequency."
        elif "amount" in primary_driver.lower() or "amount" in rule_name.lower() or "ratio" in primary_driver.lower():
            return f"Transaction{amt_str} represents a substantial ticket-size spike significantly higher than the customer's historical average."
        elif "category" in primary_driver.lower():
            return f"Transaction{amt_str} involves a novel merchant category not previously seen in this customer's purchase history."
        elif "kill_switch" in primary_driver.lower():
            return "Transaction was blocked immediately because the merchant emergency kill switch is currently active."
        else:
            return f"Flagged by risk rules: {rule_name}. Anomaly score is {risk_score:.2f} (Detailed explanation unavailable)."


_global_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Dependency / factory for Claude client."""
    global _global_claude_client
    if _global_claude_client is None:
        _global_claude_client = ClaudeClient()
    return _global_claude_client
