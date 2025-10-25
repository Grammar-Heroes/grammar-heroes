# ─────────────────────────────
# 1. Base image
# ─────────────────────────────
FROM python:3.11-slim

# ─────────────────────────────
# 2. Working directory
# ─────────────────────────────
WORKDIR /app

# ─────────────────────────────
# 3. Environment variables
# ─────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# ─────────────────────────────
# 4. System dependencies
# ─────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# ─────────────────────────────
# 5. Dependency installation
# ─────────────────────────────
COPY requirements.txt* pyproject.toml* poetry.lock* /app/

RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    elif [ -f pyproject.toml ]; then \
        pip install .; \
    else \
        pip install fastapi "uvicorn[standard]" gunicorn \
            "redis>=5,<6" "sqlalchemy[asyncio]" asyncpg alembic \
            python-multipart pydantic-settings firebase-admin; \
    fi

# ─────────────────────────────
# 6. Copy application code
# ─────────────────────────────
COPY . /app

# ─────────────────────────────
# 7. Start command
# ─────────────────────────────
# Render injects $PORT, default 10000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]