"""Consistent JSON error responses for the HTTP API."""

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from forgeflow.errors import ForgeFlowError
from forgeflow.observability.logging import get_logger

logger = get_logger(__name__)


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return payload


async def forgeflow_error_handler(_request: Request, exc: ForgeFlowError) -> JSONResponse:
    logger.warning("application_error", extra={"forgeflow": {"code": exc.code}})
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.details or None),
    )


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body("http_error", message),
    )


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body(
            "validation_error",
            "Request validation failed",
            {"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", extra={"forgeflow": {"type": type(exc).__name__}})
    return JSONResponse(
        status_code=500,
        content=error_body("internal_error", "An unexpected error occurred"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers to an application instance."""
    app.add_exception_handler(ForgeFlowError, cast(ExceptionHandler, forgeflow_error_handler))
    app.add_exception_handler(
        StarletteHTTPException, cast(ExceptionHandler, http_exception_handler)
    )
    app.add_exception_handler(
        RequestValidationError, cast(ExceptionHandler, validation_exception_handler)
    )
    app.add_exception_handler(Exception, cast(ExceptionHandler, unhandled_exception_handler))
