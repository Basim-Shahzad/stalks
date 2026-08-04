"""
Domain-level exceptions, decoupled from FastAPI/HTTP. Services and
repositories raise these; a single exception handler in main.py maps
them to HTTP responses. This keeps the domain layer testable without
importing FastAPI at all.
"""


class AppException(Exception):
    """Base class for all custom application exceptions."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when a requested resource doesn't exist."""

    pass


class ConflictException(AppException):
    """Raised on uniqueness violations or state conflicts (e.g. duplicate email)."""

    pass


class ValidationException(AppException):
    """Raised for business-rule validation failures not caught by Pydantic."""

    pass


class UnauthorizedException(AppException):
    """Raised when a user is authenticated but not permitted to perform an action."""

    pass
