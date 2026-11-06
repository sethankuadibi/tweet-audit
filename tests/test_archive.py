import json

import pytest

from tweet_audit.archive import load_tweets


def test_loads_javascript_wrapped_x_archive(tmp_path):
    records = [
        {"tweet": {"id_str": "123", "full_text": "hello", "created_at": "today"}},
        {"tweet": {"id_str": "456", "full_text": "world"}},
    ]
    archive = tmp_path / "tweets.js"
    archive.write_text("window.YTD.tweets.part0 = " + json.dumps(records), encoding="utf-8")

    tweets = load_tweets(archive)

    assert [tweet.id for tweet in tweets] == ["123", "456"]
    assert tweets[0].text == "hello"


def test_skips_malformed_records(tmp_path):
    archive = tmp_path / "tweets.json"
    archive.write_text(json.dumps([{"tweet": {"id_str": "1"}}, {"unexpected": True}]))

    assert load_tweets(archive) == []


def test_rejects_invalid_json(tmp_path):
    archive = tmp_path / "tweets.js"
    archive.write_text("not JSON")

    with pytest.raises(ValueError, match="Could not parse"):
        load_tweets(archive)

