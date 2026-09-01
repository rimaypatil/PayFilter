"""Pydantic schemas and contracts for PayFilter API."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCheckRequest(BaseModel):
    """Incoming transaction scoring payload."""

    transaction_id: str = Field(..., description="Unique UUID for this transaction")
    merchant_id: str = Field(..., description="UUID of the merchant")
    customer_id: str = Field(..., min_length=1, description="Identifier of the customer/account")
    amount: float = Field(..., gt=0.0, description="Transaction amount (must be positive)")
    timestamp: datetime = Field(..., description="ISO-8601 transaction timestamp")
    merchant_category: str = Field(..., min_length=1, description="Business category of merchant")
    agent_type: str = Field(..., min_length=1, description="AI agent type or initiator")

    model_config = ConfigDict(
        extra="forbid",  # Reject unexpected fields
        json_schema_extra={
            "example": {
                "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "merchant_id": "a0000000-0000-0000-0000-000000000001",
                "customer_id": "cust_12345",
                "amount": 250.00,
                "timestamp": "2026-08-30T12:00:00Z",
                "merchant_category": "electronics",
                "agent_type": "procurement_agent",
            }
        },
    )

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be strictly greater than 0")
        return round(float(v), 2)


class RuleResult(BaseModel):
    """Structured outcome of deterministic rule evaluation."""

    triggered: bool = Field(default=False, description="Whether any rule fired")
    rule_name: Optional[str] = Field(default=None, description="Identifier of the fired rule")
    reason: Optional[str] = Field(default=None, description="Deterministic reason for firing")
    rule_type: Optional[Literal["hard", "soft"]] = Field(default=None, description="Hard block vs soft hold")


class TransactionCheckResponse(BaseModel):
    """Decision output returned to the merchant caller."""

    transaction_id: str = Field(..., description="Transaction UUID")
    status: Literal["approved", "held", "blocked"] = Field(..., description="Scoring decision")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Normalized risk anomaly score [0.0 - 1.0]")
    reason: Dict[str, Any] = Field(..., description="Machine-readable structured explanation")
    audit_log_id: str = Field(..., description="UUID of the audit log record")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "status": "approved",
                "risk_score": 0.1245,
                "reason": {
                    "decision": "approved",
                    "primary_driver": "model_score",
                    "rule_triggered": None,
                    "model_score": 0.1245,
                    "thresholds": {"hold": 0.45, "block": 0.75},
                },
                "audit_log_id": "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
            }
        }
    )


class AuditLogEntry(BaseModel):
    """Audit log item schema."""

    id: str
    transaction_id: Optional[str] = None
    merchant_id: str
    action: str
    actor: str = "system"
    prev_hash: str
    row_hash: str
    created_at: str


class AuditLogResponse(BaseModel):
    """Paginated list of audit records."""

    items: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_version: str
    model_loaded: bool = True
