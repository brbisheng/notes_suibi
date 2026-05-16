import sqlite3
from pathlib import Path

from app.config import get_settings
from app.models import MVP_TABLE_SQL



def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_file = Path(settings.db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn



def init_db() -> None:
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_outputs_target ON llm_outputs(target_type, target_id, id DESC)")
        conn.commit()
