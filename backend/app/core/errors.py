import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.request_id import get_request_id
from app.services.errors import (
    OrganizationNotFoundError,
    OrganizationSlugConflictError,
)

logger = logging.getLogger("trustrail.errors")


def _envelope(code: str, message: str) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": get_request_id(),
        }
    }


async def _not_found_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=_envelope("ORGANIZATION_NOT_FOUND", "The organization could not be found."),
    )


async def _slug_conflict_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=_envelope(
            "ORGANIZATION_SLUG_CONFLICT", "An organization with this slug already exists."
        ),
    )


async def _validation_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_envelope("VALIDATION_ERROR", "The request payload failed validation."),
    )


async def _http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return await _unhandled_exception_handler(_request, exc)
    code = exc.detail if isinstance(exc.detail, str) else "HTTP_ERROR"
    message = exc.detail if isinstance(exc.detail, str) else "Request could not be completed."
    return JSONResponse(status_code=exc.status_code, content=_envelope(code, message))


async def _unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    # Log server-side; never leak internals or tracebacks to the caller.
    logger.exception("Unhandled exception: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=_envelope("INTERNAL_ERROR", "An internal error occurred."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(OrganizationNotFoundError, _not_found_handler)
    app.add_exception_handler(OrganizationSlugConflictError, _slug_conflict_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
