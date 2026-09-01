-- Migration: 0002_create_transactions.sql
-- Description: Create transactions table with risk scoring results and metadata.

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    customer_id TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('approved', 'held', 'blocked')),
    risk_score NUMERIC(5, 4) NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    reason JSONB NOT NULL,
    model_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id ON transactions (merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions (merchant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions (created_at DESC);
