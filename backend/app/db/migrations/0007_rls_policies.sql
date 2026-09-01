-- Migration: 0007_rls_policies.sql
-- Description: Define Row-Level Security policies for multi-tenant isolation.

-- Helper function to extract current merchant_id from JWT claims or session variable
CREATE OR REPLACE FUNCTION current_merchant_id()
RETURNS UUID AS $$
BEGIN
    -- First try custom session setting (useful for direct DB connections / testing)
    IF NULLIF(current_setting('app.current_merchant_id', true), '') IS NOT NULL THEN
        RETURN current_setting('app.current_merchant_id', true)::UUID;
    END IF;
    
    -- Next try Supabase JWT claim
    IF auth.jwt() ->> 'merchant_id' IS NOT NULL THEN
        RETURN (auth.jwt() ->> 'merchant_id')::UUID;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Service role bypass policies (service_role can manage all records)
CREATE POLICY service_role_merchants_all ON merchants
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_role_transactions_all ON transactions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_role_audit_log_all ON audit_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_role_rules_config_all ON rules_config
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Tenant Isolation Policies for Merchants
CREATE POLICY merchant_isolation_merchants_select ON merchants
    FOR SELECT TO authenticated, anon
    USING (id = current_merchant_id());

-- Tenant Isolation Policies for Transactions
CREATE POLICY merchant_isolation_transactions_select ON transactions
    FOR SELECT TO authenticated, anon
    USING (merchant_id = current_merchant_id());

CREATE POLICY merchant_isolation_transactions_insert ON transactions
    FOR INSERT TO authenticated, anon
    WITH CHECK (merchant_id = current_merchant_id());

-- Tenant Isolation Policies for Audit Log (SELECT and INSERT only)
CREATE POLICY merchant_isolation_audit_log_select ON audit_log
    FOR SELECT TO authenticated, anon
    USING (merchant_id = current_merchant_id());

CREATE POLICY merchant_isolation_audit_log_insert ON audit_log
    FOR INSERT TO authenticated, anon
    WITH CHECK (merchant_id = current_merchant_id());

-- Tenant Isolation Policies for Rules Config
CREATE POLICY merchant_isolation_rules_config_select ON rules_config
    FOR SELECT TO authenticated, anon
    USING (merchant_id = current_merchant_id());

CREATE POLICY merchant_isolation_rules_config_update ON rules_config
    FOR UPDATE TO authenticated, anon
    USING (merchant_id = current_merchant_id())
    WITH CHECK (merchant_id = current_merchant_id());
