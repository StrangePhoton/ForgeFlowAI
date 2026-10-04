"""Checkpoint backends for investigation graphs."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from forgeflow.config import Settings


@asynccontextmanager
async def open_checkpointer(settings: Settings) -> AsyncIterator[Any]:
    """Yield a MemorySaver or a PostgreSQL checkpointer based on settings."""
    if settings.checkpoint_backend == "postgres":
        async with AsyncPostgresSaver.from_conn_string(settings.psycopg_database_url) as saver:
            await saver.setup()
            yield saver
    else:
        yield MemorySaver()
