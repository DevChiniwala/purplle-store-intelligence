"""Structured-logging middleware using structlog.

Logs every HTTP request/response with timing, status, method, path, and the
correlation ID injected by the tracing middleware.
"""

import time
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from api.middleware.tracing import correlation_id_ctx

logger = structlog.get_logger("api.access")


def configure_structlog() -> None:
    """Set up structlog with JSON rendering and stdlib integration."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _inject_correlation_id,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _inject_correlation_id(
    _logger: Any,
    _method: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that adds the correlation ID to every log line."""
    cid = correlation_id_ctx.get("")
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status code, and latency for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        log = logger.bind(method=method, path=path)
        log.info("request.started")

        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.exception("request.failed", duration_ms=elapsed_ms)
            raise

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "request.completed",
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )
        return response
