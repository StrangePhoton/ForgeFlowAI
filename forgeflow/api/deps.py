"""FastAPI dependencies."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.providers.factory import create_llm_provider
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.services.industrial import IndustrialQueryService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    async with database.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_industrial_service(session: SessionDep) -> IndustrialQueryService:
    return IndustrialQueryService(session)


IndustrialServiceDep = Annotated[IndustrialQueryService, Depends(get_industrial_service)]


def get_llm_provider(request: Request) -> LLMProvider:
    provider = getattr(request.app.state, "llm_provider", None)
    if provider is None:
        provider = create_llm_provider(get_settings())
        request.app.state.llm_provider = provider
    return cast(LLMProvider, provider)


LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]
