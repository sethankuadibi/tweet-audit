from __future__ import annotations

import asyncio
import json
import random
from typing import Any, Self

import httpx

from .models import AuditResult, Tweet


class GeminiError(RuntimeError):
    pass


class GeminiClient:
    def __init__(self, api_key: str, model: str, max_retries: int, timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def audit(self, tweet: Tweet, criteria: dict[str, Any]) -> AuditResult:
        prompt = (
            "Evaluate the post against the supplied alignment criteria. "
            "Return JSON only: {\"flagged\": boolean, \"reason\": string}.\n"
            f"Criteria: {json.dumps(criteria, ensure_ascii=False)}\n"
            f"Post: {tweet.text}"
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
        }
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(url, json=payload)
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        "transient Gemini response", request=response.request, response=response
                    )
                response.raise_for_status()
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return AuditResult(tweet.id, bool(parsed["flagged"]), str(parsed["reason"]))
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                if attempt + 1 == self.max_retries:
                    raise GeminiError(f"Gemini request failed after {self.max_retries} attempts") from exc
                await asyncio.sleep((2**attempt) + random.uniform(0, 0.5))
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise GeminiError("Gemini returned an unexpected response") from exc
        raise AssertionError("unreachable")
