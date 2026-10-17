FROM node:24-slim AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /bin/uv
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --frozen --no-dev
COPY configs/ configs/
COPY data/fixtures/ data/fixtures/
COPY --from=frontend /app/web/dist web/dist
RUN uv run --no-sync python -m patchpulse build-demo && useradd --uid 10001 --create-home patchpulse && chown -R patchpulse:patchpulse /app
USER patchpulse
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "patchpulse.api:app", "--host", "0.0.0.0", "--port", "8000"]
