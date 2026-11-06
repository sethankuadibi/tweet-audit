from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .archive import load_tweets
from .checkpoint import Checkpoint
from .client import GeminiClient
from .config import load_settings
from .service import process_tweets, write_flagged_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit an X archive with Gemini")
    parser.add_argument("archive", type=Path, help="Path to data/tweets.js from an X archive")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--output", type=Path, default=Path("flagged_tweets.csv"))
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoint.json"))
    return parser


async def run(args: argparse.Namespace) -> int:
    settings = load_settings(args.config)
    tweets = load_tweets(args.archive)
    checkpoint = Checkpoint(args.checkpoint)
    async with GeminiClient(settings.gemini_api_key, settings.gemini_model, settings.max_retries) as client:
        results = await process_tweets(tweets, settings, client, checkpoint)
    count = write_flagged_csv(results, settings.username, args.output)
    print(f"Audited {len(results)} tweets; wrote {count} flagged tweets to {args.output}")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    try:
        raise SystemExit(asyncio.run(run(args)))
    except (TypeError, ValueError, OSError) as exc:
        raise SystemExit(f"error: {exc}") from exc


if __name__ == "__main__":
    main()
