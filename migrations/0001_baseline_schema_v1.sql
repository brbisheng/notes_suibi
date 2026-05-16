-- Baseline schema checkpoint (v1)
-- Source of truth remains app/models.py + app/db.py bootstrap.
-- This script documents the naming policy transition and can be used
-- as a starting point for future machine-to-machine upgrades.

-- Naming policy (v1):
-- 1) Status fields should end with *_status.
-- 2) Avoid duplicated semantics between boolean flags and enum/text fields.
--    e.g. entries.manual duplicates entries.source_type='manual'.
-- 3) Existing columns are kept for backward compatibility in MVP.

-- Recommended next migration examples (not executed here):
-- ALTER TABLE entries ADD COLUMN ingest_status TEXT NOT NULL DEFAULT 'pending';
-- UPDATE entries
--   SET ingest_status = CASE WHEN pending = 1 THEN 'pending' ELSE 'processed' END;
--
-- ALTER TABLE entries ADD COLUMN source_origin_status TEXT NOT NULL DEFAULT 'manual';
-- UPDATE entries
--   SET source_origin_status = source_type;
