# AEOS Platform backend — production Dockerfile (Phase 1 後續 #11)
#
# 對應 SAD-v0.1 §3.1 + ADR-0004 deployment model：
# - Phase 1: 單租戶 Docker Compose stack per customer VM
# - Image 用於 API + Worker（同一 image 不同 entrypoint）
#
# Multi-stage build：
# 1. builder：用 uv 鎖定 dependencies
# 2. runtime：slim image + non-root user + minimal layers
#
# Security:
# - non-root user
# - no shell access in production (CMD only)
# - 用 Trivy CI scan（見 .github/workflows/security.yml）

# ── Stage 1: builder ──────────────────────────────
FROM python:3.12-slim AS builder

# 安裝 uv（依專案標準）
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy lock files first for layer caching
COPY pyproject.toml uv.lock README.md ./

# 安裝 dependencies（無 dev deps）
RUN uv sync --frozen --no-dev --no-install-project

# Copy 應用程式 code
COPY app/ ./app/
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY skills/ ./skills/

# Install package
RUN uv sync --frozen --no-dev

# ── Stage 2: runtime ──────────────────────────────
FROM python:3.12-slim AS runtime

# 建非 root user (SEC §6.1)
RUN groupadd -r aeos && useradd -r -g aeos -s /sbin/nologin -d /app aeos

# Install runtime deps（libpq-dev for asyncpg；ca-certificates for HTTPS）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 從 builder 拷出虛擬環境 + code
COPY --from=builder --chown=aeos:aeos /app /app

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER aeos

# Health check (Phase 1 後續 #2)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

EXPOSE 8000

# Default: API server. Worker 用 `docker run ... python -m app.worker`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
