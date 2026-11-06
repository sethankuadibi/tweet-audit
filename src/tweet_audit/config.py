from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Settings


def load_settings(path: Path) -> Settings:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    api_key = os.environ.get("GEMINI_API_KEY") or raw.get("gemini_api_key", "")
    if not api_key or api_key == "replace-with-your-key-or-use-GEMINI_API_KEY":
        raise ValueError("Set GEMINI_API_KEY or gemini_api_key in the configuration file")
    if not raw.get("username"):
        raise ValueError("Configuration must include username")
    if not isinstance(raw.get("criteria"), dict) or not raw["criteria"]:
        raise ValueError("Configuration must include non-empty criteria")

    concurrency = int(raw.get("concurrency", 5))
    batch_size = int(raw.get("batch_size", 20))
    max_retries = int(raw.get("max_retries", 4))
    if min(concurrency, batch_size, max_retries) < 1:
        raise ValueError("concurrency, batch_size, and max_retries must be positive")

    return Settings(
        username=raw["username"],
        gemini_api_key=api_key,
        criteria=raw["criteria"],
        gemini_model=raw.get("gemini_model", "gemini-2.5-flash"),
        concurrency=concurrency,
        batch_size=batch_size,
        max_retries=max_retries,
    )

