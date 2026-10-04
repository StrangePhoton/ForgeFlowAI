"""Alembic environment. Database URL is always loaded from application settings."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from forgeflow.config import get_settings
from forgeflow.db.base import Base
from forgeflow.domain.models import (  # noqa: F401
    Alarm,
    ApprovalRequest,
    Document,
    DocumentChunk,
    Equipment,
    MaintenanceRecord,
    SensorReading,
    WorkOrder,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure_sqlalchemy_url() -> None:
    settings = get_settings()
    config.set_main_option("sqlalchemy.url", settings.async_database_url)


def run_migrations_offline() -> None:
    _configure_sqlalchemy_url()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    _configure_sqlalchemy_url()
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
