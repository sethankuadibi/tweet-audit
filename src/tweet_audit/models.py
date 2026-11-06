from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Tweet:
    id: str
    text: str
    created_at: str | None = None


@dataclass(frozen=True, slots=True)
class AuditResult:
    tweet_id: str
    flagged: bool
    reason: str


@dataclass(frozen=True, slots=True)
class Settings:
    username: str
    gemini_api_key: str
    criteria: dict[str, Any]
    gemini_model: str = "gemini-2.5-flash"
    concurrency: int = 5
    batch_size: int = 20
    max_retries: int = 4

