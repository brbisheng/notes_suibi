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
    CREATE TABLE IF NOT EXISTS raw_imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        parse_status TEXT NOT NULL,
        parse_error TEXT,
        failed_input_path TEXT,
        session_count INTEGER NOT NULL DEFAULT 0,
        turn_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_import_id INTEGER NOT NULL,
        source_session_id TEXT,
        project_path TEXT,
        metadata TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (raw_import_id) REFERENCES raw_imports(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS session_turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        turn_index INTEGER,
        source_turn_id TEXT,
        raw_refs_json TEXT,
        user_request TEXT,
        final_summary TEXT,
        timing TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
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
