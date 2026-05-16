from __future__ import annotations

from typing import Any

from app.db import get_connection


def get_recent_today_entries(limit: int = 10) -> list[Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, raw_content, record_type, tags, created_at
            FROM entries
            WHERE date = date('now', 'localtime')
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()


def get_today_entries_grouped() -> dict[str, list[Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, raw_content, record_type, tags, source_type, created_at
            FROM entries
            WHERE date = date('now', 'localtime')
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

    grouped = {"manual": [], "import": []}
    for row in rows:
        source = "manual" if row["source_type"] == "manual" else "import"
        grouped[source].append(row)
    return grouped


def search_entries(keyword: str = "", record_type: str = "", start_date: str = "", end_date: str = "") -> list[Any]:
    sql = """
        SELECT id, raw_content, record_type, tags, project, date, source_type, created_at
        FROM entries
        WHERE 1=1
    """
    params: list[Any] = []

    if keyword.strip():
        sql += " AND (raw_content LIKE ? OR tags LIKE ? OR project LIKE ?)"
        pattern = f"%{keyword.strip()}%"
        params.extend([pattern, pattern, pattern])

    if record_type.strip():
        sql += " AND record_type = ?"
        params.append(record_type.strip())

    if start_date.strip():
        sql += " AND date >= ?"
        params.append(start_date.strip())

    if end_date.strip():
        sql += " AND date <= ?"
        params.append(end_date.strip())

    sql += " ORDER BY date DESC, created_at DESC LIMIT 200"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
