# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
import os
load_dotenv() 

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url():
    # 1. Try to get a specific sync URL first
    url = os.getenv("DATABASE_URL_SYNC")
    
    # 2. If not found, get the main one
    if not url:
        url = os.getenv("DATABASE_URL")
        
    # 3. SAFETY FIX: If the URL says "asyncpg", switch it to standard "psycopg"
    # This lets Alembic run synchronously while your App runs asynchronously.
    if url and "asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg") 
        # Or just url.replace("+asyncpg", "") if you rely on the default driver
        
    return url


from app.core.db import Base
from app.models import user, adventure, stats  # ensure models are imported

target_metadata = Base.metadata


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()