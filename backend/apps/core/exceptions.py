"""Consistent API error envelope: {"detail": ..., "errors": ...}."""
import logging

from rest_framework.views import exception_handler

logger = logging.getLogger("core")


def api_exception_handler(exc, context):
    """DRF exception handler that logs server errors and normalizes the body."""
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        from rest_framework.exceptions import APIException

        return exception_handler(
            APIException("An unexpected error occurred. Please try again later."), context
        )
    return response
