FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt* pyproject.toml* poetry.lock* /app/
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; \
    elif [ -f pyproject.toml ]; then pip install .; \
    else pip install fastapi "uvicorn[standard]" gunicorn \
         "redis>=5,<6" "sqlalchemy[asyncio]" asyncpg alembic python-multipart; fi
COPY . /app
# Render overrides the port via startCommand; no EXPOSE needed