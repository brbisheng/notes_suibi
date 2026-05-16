from __future__ import annotations

import httpx

from app.config import get_settings
from app.llm.base import LLMResult
from app.llm.prompts import ORGANIZE_SYSTEM_PROMPT


class OpenRouterClient:
    def __init__(self, model: str = "openai/gpt-4o-mini"):
        self.model = model
        self.api_key = get_settings().openrouter_api_key

    def complete_json(self, prompt: str) -> LLMResult:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ORGANIZE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        model_name = data.get("model", self.model)
        return LLMResult(content=content, model=model_name)
