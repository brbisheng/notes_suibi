from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.db import get_connection
from app.llm.openrouter import OpenRouterClient
from app.llm.prompts import build_entry_prompt, build_turn_prompt


REQUIRED_KEYS = {"summary", "category", "action_items", "tags", "is_life_insight"}


def _validate_output(obj: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_KEYS - set(obj.keys())
    if missing:
        raise ValueError(f"LLM output missing keys: {', '.join(sorted(missing))}")
    return obj


def run_entry_organize(entry_id: int) -> None:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = c.fetchone()
        if row is None:
            raise ValueError("entry not found")

    prompt = build_entry_prompt(row["raw_content"], row["record_type"], row["tags"])
    result = OpenRouterClient().complete_json(prompt)
    parsed = _validate_output(json.loads(result.content))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO llm_outputs (
                target_type, target_id, summary, category, action_items_json,
                tags_json, is_life_insight, model, raw_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "entry",
                entry_id,
                parsed["summary"],
                parsed["category"],
                json.dumps(parsed["action_items"], ensure_ascii=False),
                json.dumps(parsed["tags"], ensure_ascii=False),
                1 if parsed["is_life_insight"] else 0,
                result.model,
                json.dumps(parsed, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()


def run_turn_organize(turn_id: int) -> None:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM session_turns WHERE id = ?", (turn_id,))
        row = c.fetchone()
        if row is None:
            raise ValueError("turn not found")

    prompt = build_turn_prompt(row["user_request"], row["final_summary"])
    result = OpenRouterClient().complete_json(prompt)
    parsed = _validate_output(json.loads(result.content))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO llm_outputs (
                target_type, target_id, summary, category, action_items_json,
                tags_json, is_life_insight, model, raw_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "turn",
                turn_id,
                parsed["summary"],
                parsed["category"],
                json.dumps(parsed["action_items"], ensure_ascii=False),
                json.dumps(parsed["tags"], ensure_ascii=False),
                1 if parsed["is_life_insight"] else 0,
                result.model,
                json.dumps(parsed, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
