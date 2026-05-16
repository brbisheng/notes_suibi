-- Align session_turns with documented status field semantics.
-- app/db.py already applies this idempotently.
ALTER TABLE session_turns ADD COLUMN llm_status TEXT NOT NULL DEFAULT 'pending';
