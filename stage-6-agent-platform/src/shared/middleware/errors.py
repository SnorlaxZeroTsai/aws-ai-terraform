"""
Error handling middleware for FastAPI.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors globally."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            logger.error(f"Unhandled error: {exc}", exc_info=True)

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(exc) if logger.level == logging.DEBUG else "An error occurred"
                }
            )
