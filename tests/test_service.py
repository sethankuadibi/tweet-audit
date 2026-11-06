import csv

from tweet_audit.checkpoint import Checkpoint
from tweet_audit.models import AuditResult, Settings, Tweet
from tweet_audit.service import process_tweets, write_flagged_csv


class FakeAuditor:
    def __init__(self):
        self.calls = []

    async def audit(self, tweet, criteria):
        self.calls.append(tweet.id)
        return AuditResult(tweet.id, "flag" in tweet.text, "test reason")


async def test_processes_and_checkpoints_tweets(tmp_path):
    settings = Settings("seth", "key", {"tone": "kind"}, concurrency=2, batch_size=2)
    tweets = [Tweet("1", "fine"), Tweet("2", "flag me")]
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    auditor = FakeAuditor()

    results = await process_tweets(tweets, settings, auditor, checkpoint)

    assert len(results) == 2
    assert set(checkpoint.results) == {"1", "2"}

    second_auditor = FakeAuditor()
    await process_tweets(tweets, settings, second_auditor, Checkpoint(checkpoint.path))
    assert second_auditor.calls == []


def test_writes_only_flagged_results(tmp_path):
    output = tmp_path / "flagged.csv"
    results = [AuditResult("1", False, "fine"), AuditResult("2", True, "review")]

    count = write_flagged_csv(results, "seth", output)

    with output.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert count == 1
    assert rows == [{"tweet_url": "https://x.com/seth/status/2", "deleted": "false", "reason": "review"}]

