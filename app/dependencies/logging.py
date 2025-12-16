"""Dependencies for logging."""

from fastapi import Request
from loguru import logger


def get_request_logger(request: Request = None):
    """Dependency to retrieve the request-scoped loguru logger."""
    if request and hasattr(request.state, "request_id"):
        request_id = getattr(request.state, "request_id")
    else:
        request_id = "N/A_OUTSIDE_REQUEST"

    return logger.bind(request_id=request_id)
