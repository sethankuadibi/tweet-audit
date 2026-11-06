# Tweet Audit

A resilient Python app that reviews an exported X (Twitter) archive against your own
alignment criteria using Google Gemini, then produces a CSV for manual review. Use the
browser interface for the easiest experience or the CLI for automation.

> Tweet Audit never deletes posts and does not require X API credentials.

## Why this project?

This project demonstrates production-oriented backend techniques on a practical workflow:
asynchronous HTTP, bounded concurrency, retries with jitter, resumable processing, atomic
checkpoint writes, dependency boundaries, and tests without paid API calls.

## How it works

```text
tweets.js -> parse -> skip completed -> concurrent Gemini audit -> checkpoint
                                                          |
                                                          v
                                                flagged_tweets.csv
```

See [ARCHITECTURE.md](ARCHITECTURE.md), [ALGORITHMS.md](ALGORITHMS.md), and
[TRADEOFFS.md](TRADEOFFS.md) for the engineering decisions behind the implementation.

## Requirements

- Python 3.11+
- An [X data archive](https://help.x.com/en/managing-your-account/how-to-download-your-x-archive)
- A Gemini API key

## Setup

```bash
git clone https://github.com/sethankuadibi/tweet-audit.git
cd tweet-audit
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp config.example.json config.json
export GEMINI_API_KEY='your-key'
```

Edit `config.json` to set your X username and criteria. Do not commit that file.

## Usage

### Browser interface

```bash
streamlit run streamlit_app.py
```

Open the displayed local URL, upload `data/tweets.js`, enter your username, Gemini key, and
review rules, then download the result. The browser workflow does not write the upload or key
to disk.

For a one-command container setup:

```bash
docker compose up --build
```

Then open <http://localhost:8501>. The container runs as a non-root user with a read-only root
filesystem, dropped Linux capabilities, and an application health check.

### Command line

Locate `data/tweets.js` inside your extracted X archive, then run:

```bash
tweet-audit /path/to/archive/data/tweets.js
```

Optional paths:

```bash
tweet-audit tweets.js \
  --config config.json \
  --output flagged_tweets.csv \
  --checkpoint checkpoint.json
```

If processing is interrupted, run the same command again. Completed tweet IDs are read from
the checkpoint and will not be sent to Gemini twice.

## Output

```csv
tweet_url,deleted,reason
https://x.com/username/status/1234567890,false,Contains a configured forbidden word
```

Review each post manually before taking action. Model output can be wrong.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Tests use fakes and HTTP mocks; they never call Gemini or incur API costs.

## DevOps

```bash
make help     # List common development and operations commands
make check    # Run lint and tests
make build    # Build the production image
make up       # Run the hardened local stack
```

GitHub Actions tests Python 3.11–3.13, builds the container, and runs CodeQL analysis.
Dependabot monitors Python, Docker, and GitHub Actions dependencies. See
[OPERATIONS.md](OPERATIONS.md) for health checks, deployment expectations, observability, and
incident actions.

## Privacy

Post text is sent to Gemini for evaluation. Archive files, generated CSV files, checkpoints,
local configuration, and environment files are excluded through `.gitignore`.

## License

MIT
