"""Async SQLAlchemy engine and session factory."""

import asyncio
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from forgeflow.config import Settings


class Database:
    """Process-scoped async database access.

    The engine is created at startup. Connections are opened only when a
    session or ping is requested, so liveness checks do not require Postgres.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.engine: AsyncEngine = create_async_engine(
            settings.async_database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout_seconds,
            pool_pre_ping=True,
            echo=settings.database_echo,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    async def ping(self) -> None:
        """Verify that PostgreSQL accepts a simple query."""
        async with asyncio.timeout(self._settings.database_ping_timeout_seconds):
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as db_session:
            yield db_session

    async def dispose(self) -> None:
        await self.engine.dispose()
