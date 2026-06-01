"""Correlation-ID / request-ID tracing middleware."""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable holding the current correlation ID – accessible anywhere in
# the async call-chain without threading issues.
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

HEADER_NAME = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Inject or propagate a correlation ID on every request/response cycle."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use an incoming header if present, otherwise mint a new UUID4.
        incoming_id: str = request.headers.get(HEADER_NAME, "")
        cid = incoming_id if incoming_id else str(uuid.uuid4())
        token = correlation_id_ctx.set(cid)

        try:
            response: Response = await call_next(request)
            response.headers[HEADER_NAME] = cid
            return response
        finally:
            correlation_id_ctx.reset(token)
