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

-- 5. Seed Customer Historical Baselines (for feature extraction)
-- cust_demo_normal: consistent historical purchases of ~400-600 INR
INSERT INTO transactions (id, merchant_id, customer_id, amount, agent_type, status, risk_score, reason, model_version, created_at)
VALUES 
    ('11111111-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'cust_demo_normal', 450.00, 'grocery_bot', 'approved', 0.12, '{"decision": "approved"}'::jsonb, 'v1.0.0', NOW() - INTERVAL '5 days'),
    ('11111111-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'cust_demo_normal', 520.00, 'grocery_bot', 'approved', 0.14, '{"decision": "approved"}'::jsonb, 'v1.0.0', NOW() - INTERVAL '2 days'),
    ('11111111-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'cust_demo_normal', 480.00, 'grocery_bot', 'approved', 0.11, '{"decision": "approved"}'::jsonb, 'v1.0.0', NOW() - INTERVAL '1 day')
ON CONFLICT (id) DO NOTHING;

-- cust_demo_burst: primed with recent transactions to test velocity triggers
INSERT INTO transactions (id, merchant_id, customer_id, amount, agent_type, status, risk_score, reason, model_version, created_at)
VALUES 
    ('22222222-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'cust_demo_burst', 1200.00, 'shopper_agent', 'approved', 0.20, '{"decision": "approved"}'::jsonb, 'v1.0.0', NOW() - INTERVAL '2 minutes'),
    ('22222222-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'cust_demo_burst', 1200.00, 'shopper_agent', 'approved', 0.25, '{"decision": "approved"}'::jsonb, 'v1.0.0', NOW() - INTERVAL '1 minute')
ON CONFLICT (id) DO NOTHING;

-- cust_demo_borderline: seeded with baseline that puts a 4,800 INR purchase in the hold band (0.45 <= score < 0.70)
INSERT INTO transactions (id, merchant_id, customer_id, amount, agent_type, status, risk_score, reason, model_version, created_at)
VALUES 
    ('33333333-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'cust_demo_borderline', 1500.00, 'procurement_bot', 'approved', 0.22, '{"decision": "approved"}'::jsonb, 'v1.0.0', NOW() - INTERVAL '10 days')
ON CONFLICT (id) DO NOTHING;
