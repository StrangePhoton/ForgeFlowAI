"""HTTP middleware for request correlation."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from forgeflow.observability.logging import set_request_id


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
