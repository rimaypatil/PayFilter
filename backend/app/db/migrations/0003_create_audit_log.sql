-- Migration: 0003_create_audit_log.sql
-- Description: Create append-only cryptographic audit log table with DB-level mutation prevention.

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    prev_hash TEXT NOT NULL,
    row_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_merchant_created ON audit_log (merchant_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_audit_log_transaction_id ON audit_log (transaction_id);

-- Enforce append-only at the database privilege level
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE audit_log FROM authenticated, anon, public;
GRANT SELECT, INSERT ON TABLE audit_log TO authenticated, anon, service_role;

-- Enforce append-only via trigger for defense-in-depth across all roles
CREATE OR REPLACE FUNCTION forbid_audit_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is strictly append-only. UPDATE and DELETE operations are forbidden.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_audit_log_mutation ON audit_log;
CREATE TRIGGER trg_prevent_audit_log_mutation
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW
EXECUTE FUNCTION forbid_audit_log_mutation();
