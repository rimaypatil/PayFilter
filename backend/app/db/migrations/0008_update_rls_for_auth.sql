-- Migration: 0008_update_rls_for_auth.sql
-- Description: Update Row-Level Security policies to bind directly to authenticated user_roles via auth.uid().

-- Helper function to resolve merchant_id for current authenticated user
CREATE OR REPLACE FUNCTION auth_user_merchant_id()
RETURNS UUID AS $$
DECLARE
    m_id UUID;
BEGIN
    SELECT merchant_id INTO m_id
    FROM user_roles
    WHERE user_id = auth.uid()
    LIMIT 1;

    RETURN m_id;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Drop old policies from 0007_rls_policies.sql
DROP POLICY IF EXISTS merchant_isolation_merchants_select ON merchants;
DROP POLICY IF EXISTS merchant_isolation_transactions_select ON transactions;
DROP POLICY IF EXISTS merchant_isolation_transactions_insert ON transactions;
DROP POLICY IF EXISTS merchant_isolation_audit_log_select ON audit_log;
DROP POLICY IF EXISTS merchant_isolation_audit_log_insert ON audit_log;
DROP POLICY IF EXISTS merchant_isolation_rules_config_select ON rules_config;
DROP POLICY IF EXISTS merchant_isolation_rules_config_update ON rules_config;

-- Enable RLS on user_roles
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;

CREATE POLICY service_role_user_roles_all ON user_roles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY user_roles_self_select ON user_roles
    FOR SELECT TO authenticated
    USING (user_id = auth.uid() OR merchant_id = auth_user_merchant_id());

-- Real auth.uid()-based policies across tables
CREATE POLICY auth_merchants_select ON merchants
    FOR SELECT TO authenticated
    USING (id = auth_user_merchant_id());

CREATE POLICY auth_transactions_select ON transactions
    FOR SELECT TO authenticated
    USING (merchant_id = auth_user_merchant_id());

CREATE POLICY auth_transactions_insert ON transactions
    FOR INSERT TO authenticated
    WITH CHECK (merchant_id = auth_user_merchant_id());

CREATE POLICY auth_transactions_update ON transactions
    FOR UPDATE TO authenticated
    USING (merchant_id = auth_user_merchant_id())
    WITH CHECK (merchant_id = auth_user_merchant_id());

CREATE POLICY auth_audit_log_select ON audit_log
    FOR SELECT TO authenticated
    USING (merchant_id = auth_user_merchant_id());

CREATE POLICY auth_audit_log_insert ON audit_log
    FOR INSERT TO authenticated
    WITH CHECK (merchant_id = auth_user_merchant_id());

CREATE POLICY auth_rules_config_select ON rules_config
    FOR SELECT TO authenticated
    USING (merchant_id = auth_user_merchant_id());

CREATE POLICY auth_rules_config_update ON rules_config
    FOR UPDATE TO authenticated
    USING (merchant_id = auth_user_merchant_id())
    WITH CHECK (merchant_id = auth_user_merchant_id());
