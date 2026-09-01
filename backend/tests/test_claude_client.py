"""Unit tests for Claude natural language risk explanations & PII data minimization."""

import pytest
from unittest.mock import MagicMock, patch

from backend.app.integrations.claude_client import ClaudeClient


def test_claude_fallback_explanation_generation():
    """Verifies that Claude client produces clean, non-empty explanations using fallback logic."""
    client = ClaudeClient(api_key=None)  # No API key provided -> deterministic fallback
    
    scorer_output = {
        "decision": "held",
        "primary_driver": "burst_velocity",
        "rule_triggered": "velocity_limit_exceeded",
        "risk_score": 0.58,
    }
    
    explanation = client.explain_decision(scorer_output, amount=4500.0, category="electronics", agent_type="shopper")
    assert explanation is not None
    assert len(explanation) > 10
    assert "velocity" in explanation.lower() or "flagged" in explanation.lower()


def test_claude_timeout_and_error_graceful_fallback():
    """Verifies that if Anthropic API times out or raises an error, a clean fallback string is returned."""
    client = ClaudeClient(api_key="mock-key-for-test", timeout=0.1)
    
    # Mock Anthropic SDK to raise a Timeout exception
    mock_sdk = MagicMock()
    mock_sdk.messages.create.side_effect = Exception("Request timed out after 5.0 seconds")
    client._client = mock_sdk
    
    scorer_output = {
        "decision": "blocked",
        "primary_driver": "ticket_size_spike",
        "rule_triggered": "amount_ratio_spike",
        "risk_score": 0.88,
    }
    
    # Must NOT raise exception
    explanation = client.explain_decision(scorer_output, amount=75000.0, category="luxury")
    assert explanation is not None
    assert "spike" in explanation.lower() or "flagged" in explanation.lower() or "amount" in explanation.lower()


def test_claude_data_minimization_pii_exclusion():
    """Security Test: Asserts outgoing prompt to Claude excludes any raw customer PII."""
    client = ClaudeClient(api_key="mock-key-for-test")
    
    captured_prompts = []
    
    def fake_create(**kwargs):
        messages = kwargs.get("messages", [])
        for m in messages:
            captured_prompts.append(m.get("content", ""))
        mock_resp = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "This purchase was held because the amount exceeds historical baseline."
        mock_resp.content = [mock_block]
        return mock_resp
    
    mock_sdk = MagicMock()
    mock_sdk.messages.create.side_effect = fake_create
    client._client = mock_sdk
    
    scorer_output = {
        "decision": "held",
        "primary_driver": "novel_category",
        "rule_triggered": None,
        "risk_score": 0.62,
    }
    
    explanation = client.explain_decision(
        scorer_output=scorer_output,
        amount=1200.0,
        category="gaming",
        agent_type="procurement_agent",
    )
    
    assert len(captured_prompts) > 0
    prompt_text = captured_prompts[0].lower()
    
    # Assert STRICT PII EXCLUSIONS:
    forbidden_pii_keys = [
        "customer_name", "first_name", "last_name", "email",
        "credit_card", "card_number", "cvv", "billing_address",
        "shipping_address", "phone_number", "ssn", "password"
    ]
    
    for pii in forbidden_pii_keys:
        assert pii not in prompt_text, f"Security Violation: '{pii}' detected in Claude prompt payload!"
