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
        conn.commit()
