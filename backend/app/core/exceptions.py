from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainException(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class EmailAlreadyExistsError(DomainException):
    def __init__(self, message: str = "Email address already registered."):
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidCredentialsError(DomainException):
    def __init__(self, message: str = "Invalid email address or password."):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InvalidTokenError(DomainException):
    def __init__(self, message: str = "Could not validate credentials or token expired."):
        super().__init__(
            code="INVALID_TOKEN",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UserNotFoundError(DomainException):
    def __init__(self, message: str = "User not found."):
        super().__init__(
            code="USER_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class LinkNotFoundError(DomainException):
    def __init__(self, message: str = "The requested short link does not exist or has been removed."):
        super().__init__("LINK_NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


class InvalidDestinationUrlError(DomainException):
    def __init__(self, message: str = "Destination URL must be a valid absolute HTTP or HTTPS URL."):
        super().__init__("INVALID_DESTINATION_URL", message, status.HTTP_400_BAD_REQUEST)


class ShortCodeGenerationFailedError(DomainException):
    def __init__(self):
        super().__init__("SHORT_CODE_GENERATION_FAILED", "Unable to generate a unique short code.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class IdempotencyKeyMisuseError(DomainException):
    def __init__(self):
        super().__init__("IDEMPOTENCY_KEY_MISUSE", "The idempotency key has already been used with a different request payload.")


class IdempotencyInProgressError(DomainException):
    def __init__(self):
        super().__init__("IDEMPOTENCY_REQUEST_IN_PROGRESS", "A request with this idempotency key is currently in progress.", status.HTTP_409_CONFLICT)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers exception handlers on the FastAPI application for uniform error responses."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        headers = {}
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation error",
                    "details": exc.errors(),
                }
            },
        )
