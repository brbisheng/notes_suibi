ORGANIZE_SYSTEM_PROMPT = """
你是一个笔记整理助手。你必须只输出 JSON，不要输出 Markdown。
字段必须包含：summary, category, action_items, tags, is_life_insight。
要求：
- summary: 字符串，1-3 句。
- category: 字符串。
- action_items: 字符串数组。
- tags: 字符串数组。
- is_life_insight: 布尔值。
""".strip()


def build_entry_prompt(raw_content: str, record_type: str, tags: str | None) -> str:
    return (
        "请整理以下 entry 文本并返回 JSON:\n"
        f"record_type={record_type}\n"
        f"tags={tags or ''}\n"
        f"raw_content={raw_content}\n"
    )


def build_turn_prompt(user_request: str | None, final_summary: str | None) -> str:
    return (
        "请整理以下 session turn 文本并返回 JSON:\n"
        f"user_request={user_request or ''}\n"
        f"final_summary={final_summary or ''}\n"
    )
