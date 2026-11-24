"""HTTP middleware for request correlation and metrics."""

import uuid
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from forgeflow.config import get_settings
from forgeflow.observability.logging import set_request_id
from forgeflow.observability.metrics import record_http_request

_SKIP_METRICS_PATHS = frozenset({"/metrics"})


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign or propagate an X-Request-ID header for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            set_request_id(None)
        response.headers["X-Request-ID"] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record request count and duration for real HTTP operations."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_METRICS_PATHS:
            return await call_next(request)
        started = perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            record_http_request(
                request.method,
                _route_template(request),
                str(status),
                perf_counter() - started,
            )


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if not isinstance(template, str) or not template:
        return request.url.path
    prefix = get_settings().api_prefix.rstrip("/")
    if prefix and request.url.path.startswith(prefix) and not template.startswith(prefix):
        return f"{prefix}{template}" if template.startswith("/") else f"{prefix}/{template}"
    return template
