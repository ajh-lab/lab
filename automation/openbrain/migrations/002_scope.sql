-- OpenBrain migration 002: multi-project scopes + provenance support
-- Applies to the external PostgreSQL database "openbrain" on lab-pgsql01.
-- Idempotent. Existing rows land in the 'global' scope with provenance recorded
-- in metadata JSONB by the server (no column needed for provenance).

ALTER TABLE thoughts
  ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'global';

CREATE INDEX IF NOT EXISTS idx_thoughts_scope ON thoughts (scope);
