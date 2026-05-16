MVP_TABLE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_content TEXT NOT NULL,
        record_type TEXT NOT NULL,
        tags TEXT,
        project TEXT,
        date TEXT NOT NULL,
        source_type TEXT NOT NULL,
        manual INTEGER NOT NULL DEFAULT 1,
        llm_status TEXT NOT NULL,
        pending INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS auth_attempts (
        ip TEXT NOT NULL,
        session_id TEXT NOT NULL,
        fail_count INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (ip, session_id)
    );
    """,
]
