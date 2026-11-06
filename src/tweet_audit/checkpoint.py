from __future__ import annotations

import json
from pathlib import Path

from .models import AuditResult


class Checkpoint:
    def __init__(self, path: Path):
        self.path = path
        self.results: dict[str, AuditResult] = {}
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.results = {key: AuditResult(key, val["flagged"], val["reason"]) for key, val in raw.items()}

    def save(self, result: AuditResult) -> None:
        self.results[result.tweet_id] = result
        data = {key: {"flagged": val.flagged, "reason": val.reason} for key, val in self.results.items()}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)

