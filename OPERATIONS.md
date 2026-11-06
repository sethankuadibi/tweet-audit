# Operations runbook

## Service

Tweet Audit is a stateless Streamlit service listening on port `8501`. Uploaded archives and
API keys live only in the process session. The service does not require a database or volume.

## Local container deployment

```bash
make up
docker compose ps
curl --fail http://localhost:8501/_stcore/health
```

Open <http://localhost:8501>. Follow logs with `make logs` and stop with `make down`.

## Production contract

- Run the image as UID/GID `10001`.
- Keep the root filesystem read-only and provide a small writable `/tmp` tmpfs.
- Expose container port `8501` through a TLS-terminating reverse proxy or managed platform.
- Probe `/_stcore/health` for liveness and readiness.
- Do not inject a shared Gemini key; each user supplies a key for their own session.
- Set a request-body limit compatible with the configured 200 MB archive limit.
- Run one or more stateless replicas. Session state is not shared between replicas.

## Observability

Streamlit writes operational events and errors to standard output. The container runtime
should collect stdout/stderr and alert on repeated restarts or failed health checks. Never log
uploaded post text, API keys, or generated CSV content.

## Incident actions

1. Check container state and health: `docker compose ps`.
2. Inspect recent logs: `docker compose logs --tail=200 web`.
3. Restart the service: `docker compose restart web`.
4. Roll back by deploying the previous immutable image tag or Git commit.

Because the service is stateless, restarting can interrupt an active browser review but does
not risk stored user data. CLI checkpoint files are local to CLI users and are not mounted in
the web container.

