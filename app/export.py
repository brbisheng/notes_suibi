from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.query import search_entries


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def export_jsonl() -> Path:
    entries = search_entries()
    out_dir = Path("data/exports/jsonl")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"entries_{_timestamp()}.jsonl"

    with out_path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(
                json.dumps(
                    {
                        "id": e["id"],
                        "raw_content": e["raw_content"],
                        "record_type": e["record_type"],
                        "tags": e["tags"],
                        "project": e["project"],
                        "date": e["date"],
                        "source_type": e["source_type"],
                        "created_at": e["created_at"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    return out_path


def export_markdown() -> Path:
    entries = search_entries()
    out_dir = Path("data/exports/markdown")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"entries_{_timestamp()}.md"

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Entries Export\n\n")
        for e in entries:
            f.write(f"## {e['date']} | {e['record_type']}\n")
            f.write(f"- Source: {e['source_type']}\n")
            if e["tags"]:
                f.write(f"- Tags: {e['tags']}\n")
            if e["project"]:
                f.write(f"- Project: {e['project']}\n")
            f.write(f"- Created At: {e['created_at']}\n\n")
            f.write(f"{e['raw_content']}\n\n")

    return out_path
