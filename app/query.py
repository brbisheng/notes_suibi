from __future__ import annotations

from typing import Any

from app.db import get_connection


def get_recent_today_entries(limit: int = 10) -> list[Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.id, e.raw_content, e.record_type, e.tags, e.created_at, o.summary AS llm_summary, o.model AS llm_model, o.created_at AS llm_created_at
            FROM entries e
            LEFT JOIN llm_outputs o ON o.id = (
                SELECT lo.id FROM llm_outputs lo
                WHERE lo.target_type = 'entry' AND lo.target_id = e.id
                ORDER BY lo.id DESC LIMIT 1
            )
            WHERE e.date = date('now', 'localtime')
            ORDER BY e.created_at DESC
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
            SELECT e.id, e.raw_content, e.record_type, e.tags, e.source_type, e.created_at, o.summary AS llm_summary, o.model AS llm_model, o.created_at AS llm_created_at
            FROM entries e
            LEFT JOIN llm_outputs o ON o.id = (
                SELECT lo.id FROM llm_outputs lo
                WHERE lo.target_type = 'entry' AND lo.target_id = e.id
                ORDER BY lo.id DESC LIMIT 1
            )
            WHERE e.date = date('now', 'localtime')
            ORDER BY e.created_at DESC
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
        SELECT e.id, e.raw_content, e.record_type, e.tags, e.project, e.date, e.source_type, e.created_at, o.summary AS llm_summary, o.model AS llm_model, o.created_at AS llm_created_at
        FROM entries e
        LEFT JOIN llm_outputs o ON o.id = (
            SELECT lo.id FROM llm_outputs lo
            WHERE lo.target_type = 'entry' AND lo.target_id = e.id
            ORDER BY lo.id DESC LIMIT 1
        )
        WHERE 1=1
    """
    params: list[Any] = []

    if keyword.strip():
        sql += " AND (raw_content LIKE ? OR tags LIKE ? OR project LIKE ?)"
        pattern = f"%{keyword.strip()}%"
        params.extend([pattern, pattern, pattern])

    if record_type.strip():
        sql += " AND e.record_type = ?"
        params.append(record_type.strip())

    if start_date.strip():
        sql += " AND e.date >= ?"
        params.append(start_date.strip())

    if end_date.strip():
        sql += " AND e.date <= ?"
        params.append(end_date.strip())

    sql += " ORDER BY e.date DESC, e.created_at DESC LIMIT 200"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
