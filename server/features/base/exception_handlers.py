"""
FastAPI exception handlers that map domain-level exceptions to HTTP responses.
This keeps the domain layer clean of framework-specific dependencies.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from features.base.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )


async def conflict_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message},
    )


async def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message},
    )


async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message},
    )


def register_exception_handlers(app):
    """Call this once in main.py: register_exception_handlers(app)"""
    app.add_exception_handler(NotFoundException, not_found_handler)
    app.add_exception_handler(ConflictException, conflict_handler)
    app.add_exception_handler(ValidationException, validation_handler)
    app.add_exception_handler(UnauthorizedException, unauthorized_handler)
