-- Migration: 0004_create_rules_config.sql
-- Description: Create merchant-configurable risk rules table.

CREATE TABLE IF NOT EXISTS rules_config (
    merchant_id UUID PRIMARY KEY REFERENCES merchants(id) ON DELETE CASCADE,
    max_amount_per_order NUMERIC(12, 2) NOT NULL CHECK (max_amount_per_order > 0),
    max_transactions_per_minute INTEGER NOT NULL CHECK (max_transactions_per_minute > 0),
    category_limits JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
