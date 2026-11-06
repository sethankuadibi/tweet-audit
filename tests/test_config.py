import json

import pytest

from tweet_audit.config import load_settings


def test_environment_api_key_takes_precedence(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"username": "seth", "gemini_api_key": "file", "criteria": {"tone": "kind"}}))
    monkeypatch.setenv("GEMINI_API_KEY", "environment")

    settings = load_settings(path)

    assert settings.gemini_api_key == "environment"
    assert settings.username == "seth"


def test_requires_criteria(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"username": "seth", "gemini_api_key": "key", "criteria": {}}))

    with pytest.raises(ValueError, match="criteria"):
        load_settings(path)

