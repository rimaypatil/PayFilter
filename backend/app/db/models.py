"""Database entity models mirroring Supabase Postgres schema."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class Merchant(BaseModel):
    """Merchant entity."""

    id: str
    name: str
    api_key_hash: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionRecord(BaseModel):
    """Transaction record entity."""

    id: str
    merchant_id: str
    customer_id: str
    amount: float
    agent_type: str
    status: str
    risk_score: float
    reason: Dict[str, Any]
    model_version: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogRecord(BaseModel):
    """Audit log entry entity."""

    id: Optional[str] = None
    transaction_id: Optional[str] = None
    merchant_id: str
    action: str
    actor: str = "system"
    prev_hash: str
    row_hash: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RulesConfig(BaseModel):
    """Merchant rules configuration entity."""

    merchant_id: str
    max_amount_per_order: float = Field(default=50000.0)
    max_transactions_per_minute: int = Field(default=5)
    category_limits: Dict[str, float] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
