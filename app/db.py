import sqlite3
from pathlib import Path

from app.config import get_settings
from app.models import MVP_TABLE_SQL

SCHEMA_VERSION = 1


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_file = Path(settings.db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def get_schema_version(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    return int(cursor.fetchone()[0])


def init_db() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        for sql in MVP_TABLE_SQL:
            cursor.execute(sql)

        cursor.execute("PRAGMA table_info(session_turns)")
        columns = {row[1] for row in cursor.fetchall()}
        if "turn_index" not in columns:
            cursor.execute("ALTER TABLE session_turns ADD COLUMN turn_index INTEGER")
        if "source_turn_id" not in columns:
            cursor.execute("ALTER TABLE session_turns ADD COLUMN source_turn_id TEXT")
        if "raw_refs_json" not in columns:
            cursor.execute("ALTER TABLE session_turns ADD COLUMN raw_refs_json TEXT")
        if "llm_status" not in columns:
            cursor.execute("ALTER TABLE session_turns ADD COLUMN llm_status TEXT NOT NULL DEFAULT 'pending'")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_outputs_target ON llm_outputs(target_type, target_id, id DESC)"
        )
        cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()
        return SCHEMA_VERSION
