# syntax=docker/dockerfile:1.7
FROM python:3.15-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_NO_CACHE_DIR=0 python -m pip wheel --wheel-dir /wheels .

FROM python:3.15-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_PORT=8501

RUN groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid app --create-home app

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install /wheels/* && rm -rf /wheels
COPY --chown=app:app streamlit_app.py ./
COPY --chown=app:app .streamlit ./.streamlit

USER 10001:10001
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"

CMD ["streamlit", "run", "streamlit_app.py"]
