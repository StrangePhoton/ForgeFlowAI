"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from forgeflow import __version__
from forgeflow.config import get_settings
from forgeflow.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    environment: str


class ReadyCheck(BaseModel):
    database: str


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    checks: ReadyCheck


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Process liveness. Does not touch PostgreSQL."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={
        503: {
            "description": "A required dependency is unavailable",
        }
    },
)
async def ready(request: Request) -> JSONResponse:
    """Process readiness. Requires a successful PostgreSQL ping."""
    database = request.app.state.database
    try:
        await database.ping()
    except Exception as exc:
        # Readiness must not 500 on driver-specific connection failures (asyncpg, etc.).
        logger.warning(
            "readiness_failed",
            extra={"forgeflow": {"error_type": type(exc).__name__}},
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {"database": "unavailable"},
                "error": {
                    "code": "dependency_unavailable",
                    "message": "Database is not reachable",
                },
            },
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "checks": {"database": "ok"}},
    )
