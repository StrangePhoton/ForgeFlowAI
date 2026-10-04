"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from forgeflow import __version__
from forgeflow.agent.checkpoints import open_checkpointer
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.factory import create_llm_provider
from forgeflow.api.errors import register_exception_handlers
from forgeflow.api.middleware import RequestIdMiddleware
from forgeflow.api.routes.equipment import router as equipment_router
from forgeflow.api.routes.health import router as health_router
from forgeflow.api.routes.investigations import router as investigations_router
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.observability.logging import configure_logging, get_logger
from forgeflow.retrieval.corpus import manuals_index

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    database = Database(settings)
    app.state.settings = settings
    app.state.database = database
    app.state.llm_provider = create_llm_provider(settings)
    app.state.approval_gate = ApprovalGate()
    app.state.document_searcher = manuals_index()
    app.state.investigations = {}
    async with open_checkpointer(settings) as checkpointer:
        app.state.checkpointer = checkpointer
        logger.info(
            "api_started",
            extra={"forgeflow": {"version": __version__, "environment": settings.environment}},
        )
        try:
            yield
        finally:
            await database.dispose()
            logger.info("api_stopped")


def create_app() -> FastAPI:
    """Build the API application. Used by uvicorn and tests."""
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(
        title="ForgeFlow AI API",
        description="Industrial agentic investigation platform HTTP API.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(health_router, prefix=settings.api_prefix)
    application.include_router(equipment_router, prefix=settings.api_prefix)
    application.include_router(investigations_router, prefix=settings.api_prefix)
    return application
