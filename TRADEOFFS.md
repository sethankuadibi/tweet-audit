# Engineering Trade-offs

## Architecture

The application uses small modules organized around a single workflow rather than a web
framework or layered enterprise architecture. Parsing, configuration, orchestration, remote
I/O, and persistence have separate responsibilities. The orchestration service depends on an
`Auditor` protocol, which keeps Gemini replaceable and makes tests deterministic.

## Concurrency

Async I/O fits a workload dominated by HTTP latency. Work is divided into bounded batches,
and a semaphore limits simultaneous calls. This is less throughput than scheduling the full
archive at once, but it prevents unbounded task and memory growth and makes API pressure
predictable. A single process is intentional; multi-process coordination would add complexity
without helping typical personal archives.

## Error Handling

Timeouts, network failures, rate limits, and selected server errors are retried using capped
exponential backoff with jitter. Permanent HTTP failures and malformed model responses fail
fast because repeating them is unlikely to help. Successful results are checkpointed
immediately, so a later failure does not discard earlier work.

## Persistence

JSON was chosen over a database for transparency and zero setup. Updates use a temporary
file followed by an atomic rename to avoid partial documents. Rewriting the checkpoint after
each result is inefficient for very large archives; SQLite would be the next step if write
volume or multi-process execution became important.

## Performance and Safety

The parser currently loads the archive into memory, trading streaming scalability for simpler
validation and control flow. That is reasonable for normal account archives. The tool only
generates recommendations: it deliberately avoids automatic deletion because model judgments
can be wrong and destructive actions require human review.

## Language and Dependencies

Python provides concise async and data-processing primitives and matches the wider project
roadmap. `httpx` is the sole runtime dependency, keeping API behavior explicit and avoiding a
vendor SDK lock-in. Standard-library CSV, JSON, CLI, and persistence tools cover the rest.

