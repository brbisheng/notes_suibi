from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    content: str
    model: str


class LLMClient(Protocol):
    def complete_json(self, prompt: str) -> LLMResult: ...
