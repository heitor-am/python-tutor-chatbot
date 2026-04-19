ARG PYTHON_VERSION=3.12
ARG GIT_SHA=dev

# ---------- Builder stage ----------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv==0.5.*

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

COPY README.md ./README.md
COPY app ./app
COPY chainlit.md ./chainlit.md
COPY .chainlit ./.chainlit

RUN uv sync --frozen --no-dev || uv sync --no-dev

# ---------- Runtime stage ----------
FROM python:${PYTHON_VERSION}-slim AS runtime

ARG GIT_SHA
ENV GIT_SHA=${GIT_SHA} \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --system --create-home --shell /bin/bash app

COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

# Chainlit's WebSocket lives at /ws — `/` returns the SPA shell which is
# enough to prove the process is up and accepting requests.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# `--host 0.0.0.0` so Fly's proxy can reach the port; `--headless` skips
# the dev-only browser-launch attempt.
CMD ["chainlit", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]
