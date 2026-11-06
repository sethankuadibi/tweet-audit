from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Protocol

from .checkpoint import Checkpoint
from .models import AuditResult, Settings, Tweet


class Auditor(Protocol):
    async def audit(self, tweet: Tweet, criteria: dict) -> AuditResult: ...


async def process_tweets(tweets: list[Tweet], settings: Settings, auditor: Auditor, checkpoint: Checkpoint) -> list[AuditResult]:
    semaphore = asyncio.Semaphore(settings.concurrency)

    async def process(tweet: Tweet) -> AuditResult:
        async with semaphore:
            result = await auditor.audit(tweet, settings.criteria)
            checkpoint.save(result)
            return result

    pending = [tweet for tweet in tweets if tweet.id not in checkpoint.results]
    for start in range(0, len(pending), settings.batch_size):
        batch = pending[start : start + settings.batch_size]
        await asyncio.gather(*(process(tweet) for tweet in batch))
    return list(checkpoint.results.values())


def write_flagged_csv(results: list[AuditResult], username: str, output: Path) -> int:
    flagged = [result for result in results if result.flagged]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["tweet_url", "deleted", "reason"])
        writer.writeheader()
        for result in flagged:
            writer.writerow({
                "tweet_url": f"https://x.com/{username}/status/{result.tweet_id}",
                "deleted": "false",
                "reason": result.reason,
            })
    return len(flagged)

