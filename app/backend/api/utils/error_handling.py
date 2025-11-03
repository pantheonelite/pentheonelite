"""Common error handling utilities for API routers."""

import structlog
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

logger = structlog.get_logger(__name__)


def handle_http_exceptions(func):
    """
    Decorator to handle HTTP exceptions consistently.

    Re-raises HTTPException, wraps other exceptions as 500 errors.
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unexpected error in endpoint", endpoint=func.__name__, error=str(e))
            raise HTTPException(status_code=500, detail=f"An error occurred: {e!s}") from e

    return wrapper


def handle_repository_errors(func):
    """
    Decorator to handle repository/database errors consistently.

    Converts SQLAlchemy errors and other database errors to appropriate HTTP responses.
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.exception("Database error in endpoint", endpoint=func.__name__, error=str(e))
            raise HTTPException(status_code=500, detail="Database operation failed") from e
        except Exception as e:
            logger.exception("Unexpected error in repository operation", endpoint=func.__name__, error=str(e))
            raise HTTPException(status_code=500, detail=f"Repository operation failed: {e!s}") from e

    return wrapper
