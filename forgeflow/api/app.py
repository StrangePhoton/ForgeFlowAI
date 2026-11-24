"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from forgeflow import __version__
from forgeflow.agent.checkpoints import open_checkpointer
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.factory import create_llm_provider
from forgeflow.api.errors import register_exception_handlers
from forgeflow.api.middleware import MetricsMiddleware, RequestIdMiddleware
from forgeflow.api.routes.audit import router as audit_router
from forgeflow.api.routes.auth import router as auth_router
from forgeflow.api.routes.equipment import router as equipment_router
from forgeflow.api.routes.health import router as health_router
from forgeflow.api.routes.investigations import router as investigations_router
from forgeflow.api.routes.metrics import router as metrics_router
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.observability.logging import configure_logging, get_logger
from forgeflow.observability.otel import configure_telemetry
from forgeflow.retrieval.corpus import manuals_index
from forgeflow.security.audit import AuditLog

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
    app.state.audit_log = AuditLog()
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
    configure_telemetry(settings)
    application = FastAPI(
        title="ForgeFlow AI API",
        description="Industrial agentic investigation platform HTTP API.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.add_middleware(MetricsMiddleware)
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    register_exception_handlers(application)
    application.include_router(metrics_router)
    application.include_router(health_router, prefix=settings.api_prefix)
    application.include_router(auth_router, prefix=settings.api_prefix)
    application.include_router(equipment_router, prefix=settings.api_prefix)
    application.include_router(investigations_router, prefix=settings.api_prefix)
    application.include_router(audit_router, prefix=settings.api_prefix)
    return application
