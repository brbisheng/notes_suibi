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


def _as_iso_like(value: Any) -> str | None:
    text = _safe_text(value)
    return text


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
            failed_count = 0
            missing_session_id_count = 0
            missing_user_request_count = 0
            missing_final_summary_count = 0
            parse_failures: list[str] = []
            sessions_map: dict[str, dict[str, Any]] = {}
            with raw_path.open("r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        if not isinstance(item, dict):
                            raise ValueError("JSON line is not an object")
                    except Exception as exc:
                        failed_count += 1
                        parse_failures.append(f"L{line_no}: {type(exc).__name__}: {str(exc)[:140]}")
                        continue

                    source_session_id = _safe_text(item.get("session_id") or item.get("conversation_id"))
                    if not source_session_id:
                        missing_session_id_count += 1
                        source_session_id = f"__missing_session__:{line_no}"
                    group_key = source_session_id

                    started_at = _as_iso_like(item.get("started_at"))
                    ended_at = _as_iso_like(item.get("ended_at"))
                    project_path = _safe_text(item.get("project_path") or item.get("cwd") or item.get("repo"))
                    user_request = _extract_user_request(item)
                    final_summary = _extract_final_summary(item)
                    if not user_request:
                        missing_user_request_count += 1
                    if not final_summary:
                        missing_final_summary_count += 1

                    source_turn_id = _safe_text(item.get("turn_id") or item.get("id") or item.get("message_id"))
                    raw_refs = item.get("refs") or item.get("references") or item.get("raw_refs")

                    if group_key not in sessions_map:
                        sessions_map[group_key] = {
                            "source_session_id": None if group_key.startswith("__missing_session__") else source_session_id,
                            "started_at": started_at,
                            "ended_at": ended_at,
                            "project_path": project_path,
                            "metadata": {
                                "models": set(),
                                "sources": set(),
                                "raw_keys": set(),
                                "line_count": 0,
                            },
                            "turns": [],
                        }

                    session_bucket = sessions_map[group_key]
                    md = session_bucket["metadata"]
                    md["line_count"] += 1
                    if item.get("model"):
                        md["models"].add(item.get("model"))
                    if item.get("source"):
                        md["sources"].add(item.get("source"))
                    md["raw_keys"].update(item.keys())

                    if project_path and not session_bucket["project_path"]:
                        session_bucket["project_path"] = project_path

                    if started_at and (not session_bucket["started_at"] or started_at < session_bucket["started_at"]):
                        session_bucket["started_at"] = started_at
                    if ended_at and (not session_bucket["ended_at"] or ended_at > session_bucket["ended_at"]):
                        session_bucket["ended_at"] = ended_at

                    session_bucket["turns"].append(
                        {
                            "user_request": user_request,
                            "final_summary": final_summary,
                            "timing": {
                                "started_at": started_at,
                                "ended_at": ended_at,
                                "duration_ms": item.get("duration_ms"),
                            },
                            "source_turn_id": source_turn_id,
                            "raw_refs_json": json.dumps(raw_refs, ensure_ascii=False) if raw_refs is not None else None,
                        }
                    )
            for session_data in sessions_map.values():
                session_count += 1
                metadata = session_data["metadata"]
                metadata_payload = {
                    "models": sorted(metadata["models"]),
                    "sources": sorted(metadata["sources"]),
                    "raw_keys": sorted(metadata["raw_keys"]),
                    "line_count": metadata["line_count"],
                    "started_at": session_data["started_at"],
                    "ended_at": session_data["ended_at"],
                }
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        raw_import_id, source_session_id, project_path, metadata, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        import_id,
                        session_data["source_session_id"],
                        session_data["project_path"],
                        json.dumps(metadata_payload, ensure_ascii=False),
                        imported_at,
                        imported_at,
                    ),
                )
                session_id = cursor.lastrowid

                for idx, turn in enumerate(session_data["turns"], start=1):
                    cursor.execute(
                        """
                        INSERT INTO session_turns (
                            session_id, turn_index, source_turn_id, raw_refs_json, user_request, final_summary, timing, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            idx,
                            turn["source_turn_id"],
                            turn["raw_refs_json"],
                            turn["user_request"],
                            turn["final_summary"],
                            json.dumps(turn["timing"], ensure_ascii=False),
                            imported_at,
                            imported_at,
                        ),
                    )
                    turn_count += 1

            parse_error_summary = {
                "failed_count": failed_count,
                "missing": {
                    "session_id": missing_session_id_count,
                    "user_request": missing_user_request_count,
                    "final_summary": missing_final_summary_count,
                },
                "failures": parse_failures[:50],
            }

            cursor.execute(
                """
                UPDATE raw_imports
                SET parse_status = ?, parse_error = ?, session_count = ?, turn_count = ?, updated_at = ?
                WHERE id = ?
                """,
                ("success", json.dumps(parse_error_summary, ensure_ascii=False), session_count, turn_count, _now_str(), import_id),
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
