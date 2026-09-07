from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.core.exceptions import InvalidCredentialsError
from backend.app.models.user import User
from backend.app.schemas.error import ErrorResponse
from backend.app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request / Validation Error"},
        409: {"model": ErrorResponse, "description": "Email Already Exists"},
        422: {"model": ErrorResponse, "description": "Unprocessable Entity"},
    },
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(),
) -> UserResponse:
    """Creates a new user account with hashed password."""
    return await auth_service.register_user(db, request)


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid Credentials"},
    },
)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(),
) -> TokenResponse:
    """
    Authenticates user credentials and returns a Bearer access token.
    Supports both JSON payload (UserLoginRequest) and Form Data (OAuth2PasswordRequestForm).
    """
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            raise InvalidCredentialsError("Invalid email address or password.")
        return await auth_service.authenticate_user(db, str(username), str(password))
    else:
        raw_body = await request.json()
        try:
            login_req = UserLoginRequest.model_validate(raw_body)
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
        return await auth_service.authenticate_user(db, login_req.email_address, login_req.password)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized / Invalid Token"},
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieves profile details for the currently authenticated caller."""
    return AuthService.get_user_profile(current_user)
