# Architecture

## Purpose

Tweet Audit is a command-line backend application that reads an exported X archive,
evaluates each post against user-defined alignment criteria with Gemini, and writes a
reviewable CSV. It never deletes posts.

## System Context

```text
X archive (tweets.js)              Google Gemini API
          |                                ^
          v                                |
    Archive parser -> Audit service -> Gemini client
                           |
                           +-> Checkpoint file
                           |
                           +-> Flagged-posts CSV -> Human review
```

The archive and API key remain on the user's machine. Only the text of a post and the
configured criteria are sent to Gemini.

## Components

### CLI (`cli.py`)

The composition root. It parses paths and options, loads configuration, constructs the
dependencies, runs the asynchronous workflow, and reports the final totals.

### Configuration (`config.py`)

Loads and validates JSON settings. `GEMINI_API_KEY` takes precedence over the JSON value
so secrets do not need to be stored in a file.

### Archive parser (`archive.py`)

Converts the JavaScript-wrapped `tweets.js` export—or equivalent plain JSON—into immutable
`Tweet` domain objects. Malformed entries without an ID or text are skipped.

### Audit service (`service.py`)

Owns orchestration. It filters completed work, divides pending posts into bounded batches,
limits simultaneous requests, records every successful result, and creates the final CSV.
It depends on an `Auditor` protocol rather than a concrete Gemini implementation, making
the workflow inexpensive to test.

### Gemini client (`client.py`)

Builds a structured prompt and calls Gemini asynchronously. It retries transient network,
rate-limit, and server failures with exponential backoff and jitter. Authentication and
other permanent HTTP failures stop immediately.

### Checkpoint store (`checkpoint.py`)

Stores results by tweet ID. Each update is written to a temporary file and atomically
renamed, reducing the chance of a corrupt checkpoint if the process stops during a write.

## Data Flow

1. The CLI validates configuration and loads the archive.
2. Previously completed IDs are read from the checkpoint.
3. Pending tweets are processed in bounded concurrent batches.
4. Each successful result is checkpointed immediately.
5. Flagged results are written as URLs to a CSV for manual review.

## Reliability and Security

- Bounded concurrency prevents uncontrolled memory and request growth.
- Retries apply only to failures likely to recover.
- Jitter reduces synchronized retry storms.
- Checkpoints make the workflow resumable and API usage idempotent by tweet ID.
- Archive files, outputs, local configuration, and environment files are ignored by Git.
- The tool does not request X credentials and cannot delete posts.

## Extension Points

The `Auditor` protocol allows another model or a deterministic local rules engine to replace
Gemini. The checkpoint implementation can later be replaced by SQLite for multi-process
coordination, while the CSV writer can be extended with JSON or HTML reports.

