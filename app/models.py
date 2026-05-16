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
]
