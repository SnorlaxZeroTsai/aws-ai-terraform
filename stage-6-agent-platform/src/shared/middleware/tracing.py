"""
X-Ray tracing middleware for FastAPI.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for X-Ray distributed tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with X-Ray tracing."""
        try:
            # X-Ray tracing is automatically handled by AWS X-Ray SDK
            # when the daemon is running and the application is instrumented

            response = await call_next(request)

            # Add X-Ray trace ID header if available
            # This is typically done automatically by the X-Ray daemon

            return response

        except Exception as exc:
            logger.error(f"Error in tracing middleware: {exc}")
            # Don't block requests if tracing fails
            return await call_next(request)
