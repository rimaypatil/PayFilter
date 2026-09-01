-- Migration: 0009_add_razorpay_order_id.sql
-- Description: Add razorpay_order_id column to transactions table for payment gateway tracking.

ALTER TABLE transactions ADD COLUMN IF NOT EXISTS razorpay_order_id TEXT;

CREATE INDEX IF NOT EXISTS idx_transactions_razorpay_order_id ON transactions (razorpay_order_id) WHERE razorpay_order_id IS NOT NULL;
