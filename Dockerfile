FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY README.md .
COPY app/ ./app/

RUN uv sync --no-dev
FROM python:3.11-slim AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]