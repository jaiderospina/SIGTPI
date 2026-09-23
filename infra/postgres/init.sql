-- SIGTPI v2.0 — PostgreSQL initialization
-- The 'sigtpi' user is created automatically by Docker via POSTGRES_USER env var.
-- This script only creates schemas and grants.

\c sigtpi

-- One schema per service
CREATE SCHEMA IF NOT EXISTS auth       AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS users      AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS academic   AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS tutoring   AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS ti         AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS sessions   AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS evaluation AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS documents  AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS similarity AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS notif      AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS reports    AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS pki        AUTHORIZATION sigtpi;
CREATE SCHEMA IF NOT EXISTS audit      AUTHORIZATION sigtpi;

-- Audit log table (shared, append-only)
CREATE TABLE IF NOT EXISTS audit.events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service     VARCHAR(64) NOT NULL,
    actor_id    UUID,
    action      VARCHAR(128) NOT NULL,
    resource    VARCHAR(128),
    resource_id UUID,
    ip_address  INET,
    payload     JSONB,
    success     BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_audit_occurred ON audit.events (occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor    ON audit.events (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_service  ON audit.events (service, action);

GRANT USAGE ON SCHEMA audit TO sigtpi;
GRANT INSERT, SELECT ON audit.events TO sigtpi;

-- Grant all schemas to sigtpi user
GRANT ALL ON SCHEMA auth, users, academic, tutoring, ti, sessions,
             evaluation, documents, similarity, notif, reports, pki TO sigtpi;

-- Set default search_path so cross-schema queries work without prefix
ALTER ROLE sigtpi SET search_path = public, users, academic, tutoring,
                                    ti, sessions, evaluation, documents,
                                    similarity, notif, reports, pki, auth;
