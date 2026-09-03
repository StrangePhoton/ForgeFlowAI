"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from forgeflow import __version__
from forgeflow.api.errors import register_exception_handlers
from forgeflow.api.middleware import RequestIdMiddleware
from forgeflow.api.routes.health import router as health_router
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    database = Database(settings)
    app.state.settings = settings
    app.state.database = database
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
    return application
