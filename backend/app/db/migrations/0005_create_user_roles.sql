-- Migration: 0005_create_user_roles.sql
-- Description: Create user_roles table for role-based access control (admin vs analyst) linked to auth.users.

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'analyst')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_roles_merchant_id ON user_roles (merchant_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles (user_id);
