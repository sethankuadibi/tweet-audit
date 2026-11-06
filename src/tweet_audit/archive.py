from __future__ import annotations

import json
from pathlib import Path

from .models import Tweet


def load_tweets(path: Path) -> list[Tweet]:
    """Load tweets from X's JavaScript-wrapped archive or plain JSON."""
    try:
        content = path.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError as exc:
        raise ValueError(f"Archive file not found: {path}") from exc

    if "=" in content and not content.startswith("["):
        content = content.split("=", 1)[1].strip()
    try:
        records = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse archive file {path}: {exc}") from exc
    if not isinstance(records, list):
        raise TypeError("Expected the archive to contain a list of tweets")

    tweets: list[Tweet] = []
    for record in records:
        data = record.get("tweet", record) if isinstance(record, dict) else {}
        tweet_id = str(data.get("id_str") or data.get("id") or "")
        text = data.get("full_text") or data.get("text")
        if tweet_id and isinstance(text, str):
            tweets.append(Tweet(tweet_id, text, data.get("created_at")))
    return tweets
