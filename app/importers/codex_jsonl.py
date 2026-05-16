import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.db import get_connection


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value)


def _extract_user_request(item: dict[str, Any]) -> str | None:
    for key in ("user_request", "prompt", "input", "text", "message"):
        text = _safe_text(item.get(key))
        if text:
            return text

    content = item.get("content")
    if isinstance(content, str):
        return _safe_text(content)
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict):
                t = part.get("text") or part.get("content")
                if isinstance(t, str):
                    chunks.append(t)
        if chunks:
            return _safe_text("\n".join(chunks))
    return None


def _extract_final_summary(item: dict[str, Any]) -> str | None:
    for key in ("final_summary", "summary", "assistant_response", "output"):
        text = _safe_text(item.get(key))
        if text:
            return text

    message = item.get("final")
    if isinstance(message, dict):
        return _safe_text(message.get("summary") or message.get("text"))
    return None


def import_codex_jsonl(upload_path: Path) -> int:
    upload_path = upload_path.resolve()
    raw_dir = Path("data/imports/raw")
    failed_dir = Path("data/imports/failed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    imported_at = _now_str()
    raw_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{upload_path.name}"
    raw_path = raw_dir / raw_name
    shutil.copy2(upload_path, raw_path)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO raw_imports (
                source, file_name, file_path, parse_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("codex_jsonl", upload_path.name, str(raw_path), "processing", imported_at, imported_at),
        )
        import_id = cursor.lastrowid
        conn.commit()

        try:
            session_count = 0
            turn_count = 0
            with raw_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)

                    source_session_id = _safe_text(item.get("session_id") or item.get("conversation_id"))
                    project_path = _safe_text(item.get("project_path") or item.get("cwd") or item.get("repo"))
                    metadata = {
                        "model": item.get("model"),
                        "source": item.get("source"),
                        "raw_keys": sorted(list(item.keys())),
                    }

                    cursor.execute(
                        """
                        INSERT INTO sessions (
                            raw_import_id, source_session_id, project_path, metadata, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            import_id,
                            source_session_id,
                            project_path,
                            json.dumps(metadata, ensure_ascii=False),
                            imported_at,
                            imported_at,
                        ),
                    )
                    session_id = cursor.lastrowid
                    session_count += 1

                    user_request = _extract_user_request(item)
                    final_summary = _extract_final_summary(item)
                    timing = {
                        "started_at": item.get("started_at"),
                        "ended_at": item.get("ended_at"),
                        "duration_ms": item.get("duration_ms"),
                    }
                    cursor.execute(
                        """
                        INSERT INTO session_turns (
                            session_id, user_request, final_summary, timing, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            user_request,
                            final_summary,
                            json.dumps(timing, ensure_ascii=False),
                            imported_at,
                            imported_at,
                        ),
                    )
                    turn_count += 1

            cursor.execute(
                """
                UPDATE raw_imports
                SET parse_status = ?, parse_error = NULL, session_count = ?, turn_count = ?, updated_at = ?
                WHERE id = ?
                """,
                ("success", session_count, turn_count, _now_str(), import_id),
            )
            conn.commit()
        except Exception as exc:
            failed_path = failed_dir / f"failed_{import_id}_{upload_path.name}"
            shutil.copy2(raw_path, failed_path)
            cursor.execute(
                """
                UPDATE raw_imports
                SET parse_status = ?, parse_error = ?, failed_input_path = ?, updated_at = ?
                WHERE id = ?
                """,
                ("failed", str(exc), str(failed_path), _now_str(), import_id),
            )
            conn.commit()

    return int(import_id)
