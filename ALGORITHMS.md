# Algorithms

## 1. Archive Parsing

X exports tweets as JavaScript rather than strict JSON:

```text
window.YTD.tweets.part0 = [ ... ]
```

The parser reads the file, removes the assignment prefix, decodes the remaining JSON array,
and normalizes every valid record into `(id, text, created_at)`.

- Time complexity: `O(n)`, where `n` is the archive size.
- Space complexity: `O(n)` because normalized tweets are retained for processing.

## 2. Resumable Work Selection

Checkpoint results are indexed by tweet ID in a hash map. Before calling Gemini, the service
filters out IDs already present in that map.

```text
pending = [tweet for tweet in archive if tweet.id not in completed_ids]
```

- Average membership lookup: `O(1)`.
- Full filtering pass: `O(t)`, where `t` is the number of tweets.
- Re-running the same archive does not spend API quota on completed posts.

## 3. Bounded Concurrent Batching

Pending tweets are divided into batches of configurable size. Tasks inside a batch execute
concurrently, while an asynchronous semaphore limits active Gemini calls.

```text
for batch in chunks(pending, batch_size):
    concurrently audit each tweet, limited by semaphore(concurrency)
    wait for the batch to finish
```

If `t` is the number of pending tweets, `b` the batch size, `c` the concurrency limit, and
`L` the average API latency, approximate processing time is `O(tL / min(b, c))`. Actual time
also depends on rate limits and retries. Memory used by active tasks is bounded by `O(b)`.

Batching provides backpressure: a very large archive cannot create hundreds of thousands of
live tasks at once.

## 4. Retry with Exponential Backoff and Jitter

Transient failures—timeouts, connection errors, HTTP 429, and selected 5xx responses—are
retried. Delay before retry number `k` is:

```text
delay = 2^k + random(0, 0.5) seconds
```

Exponential growth gives a recovering service more time after each failure. Random jitter
prevents many clients from retrying at exactly the same moment. Attempts are capped, so a
persistent outage eventually returns a clear error instead of looping forever.

Permanent failures such as an invalid API key are not retried.

## 5. Atomic Checkpoint Update

After a successful audit:

1. Add or replace the result under its tweet ID.
2. Serialize the full checkpoint to a temporary file.
3. Atomically rename the temporary file over the previous checkpoint.

The rename prevents readers from observing a partially written JSON document. The current
implementation rewrites `r` stored results per success, giving `O(r)` write work. This is a
deliberate simplicity trade-off for personal archives; SQLite would be more efficient for
very large datasets.

## 6. Flagged Result Generation

Results are scanned once. Only entries with `flagged = true` are converted into canonical
post URLs and written to CSV with `deleted = false`.

- Time complexity: `O(r)`.
- Extra space: `O(f)`, where `f` is the number of flagged results.
- The reason field makes every recommendation reviewable by a human.

