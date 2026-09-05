-- Migration: seed_demo_data.sql
-- Description: Seed initial demo merchants, rules configs, sample transactions, and named customer profiles aligned with demo-script.md.

-- 1. Demo Merchant A (Acme Electronics)
INSERT INTO merchants (id, name, api_key_hash, created_at)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'Acme Electronics',
    encode(digest('sk_live_merchant_a_key_12345', 'sha256'), 'hex'),
    NOW() - INTERVAL '30 days'
) ON CONFLICT (id) DO NOTHING;

-- 2. Demo Merchant B (Nova Retail)
INSERT INTO merchants (id, name, api_key_hash, created_at)
VALUES (
    'b0000000-0000-0000-0000-000000000002',
    'Nova Fashion',
    encode(digest('sk_live_merchant_b_key_67890', 'sha256'), 'hex'),
    NOW() - INTERVAL '30 days'
) ON CONFLICT (id) DO NOTHING;

-- 3. Rules Config for Merchant A
INSERT INTO rules_config (merchant_id, max_amount_per_order, max_transactions_per_minute, category_limits)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    50000.00,
    5,
    '{"electronics": 75000.00, "luxury": 40000.00, "gift_cards": 5000.00}'::jsonb
) ON CONFLICT (merchant_id) DO UPDATE SET
    max_amount_per_order = EXCLUDED.max_amount_per_order,
    max_transactions_per_minute = EXCLUDED.max_transactions_per_minute,
    category_limits = EXCLUDED.category_limits;

-- 4. Rules Config for Merchant B
INSERT INTO rules_config (merchant_id, max_amount_per_order, max_transactions_per_minute, category_limits)
VALUES (
    'b0000000-0000-0000-0000-000000000002',
    20000.00,
    10,
    '{"apparel": 20000.00, "luxury": 30000.00}'::jsonb
) ON CONFLICT (merchant_id) DO UPDATE SET
    max_amount_per_order = EXCLUDED.max_amount_per_order,
    max_transactions_per_minute = EXCLUDED.max_transactions_per_minute,
    category_limits = EXCLUDED.category_limits;

