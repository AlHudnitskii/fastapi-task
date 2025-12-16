"""Middleware to log requests and responses."""

import time

from fastapi import Request
from loguru import logger


async def logging_middleware(request: Request, call_next):
    """Middleware to log requests and responses."""
    start_time = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        process_time = (time.perf_counter() - start_time) * 1000

        logger.info(
            "HTTP request completed",
            method=request.method,
            path=request.url.path,
            status_code=getattr(response, "status_code", "N/A"),
            duration_ms=round(process_time, 2),
            client=request.client.host if request.client else None,
        )
