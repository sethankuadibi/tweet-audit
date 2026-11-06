import json

import httpx

from tweet_audit.client import GeminiClient
from tweet_audit.models import Tweet


async def test_parses_structured_gemini_response():
    client = GeminiClient("secret", "model", max_retries=1)

    def handler(request):
        assert "secret" in str(request.url)
        body = {"candidates": [{"content": {"parts": [{"text": json.dumps({"flagged": True, "reason": "tone"})}]}}]}
        return httpx.Response(200, json=body)

    await client._client.aclose()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await client.audit(Tweet("42", "post"), {"tone": "kind"})
    await client._client.aclose()

    assert result.flagged is True
    assert result.reason == "tone"
