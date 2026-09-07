from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse


class AuthService:
    """Service encapsulating user registration, authentication, and token management business logic."""

    def __init__(self):
        self.user_repo = UserRepository()

    async def register_user(self, db: AsyncSession, request: UserRegisterRequest) -> UserResponse:
        """
        Registers a new user.
        Raises EmailAlreadyExistsError (409 Conflict) if email is taken.
        Returns UserResponse on success.
        """
        existing_user = await self.user_repo.get_by_email(db, request.email_address)
        if existing_user:
            raise EmailAlreadyExistsError("Email address already registered.")

        hashed_pwd = hash_password(request.password)
        user = await self.user_repo.create(
            db=db,
            name=request.name,
            email_address=request.email_address,
            password_hash=hashed_pwd,
        )

        return UserResponse.model_validate(user)

    async def authenticate_user(self, db: AsyncSession, email_address: str, password: str) -> TokenResponse:
        """
        Authenticates user credentials and returns JWT Bearer access token.
        Raises InvalidCredentialsError (401 Unauthorized) if authentication fails.
        """
        user = await self.user_repo.get_by_email(db, email_address)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email address or password.")

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        access_token = create_access_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    @staticmethod
    def get_user_profile(user: User) -> UserResponse:
        """Converts domain User entity to UserResponse schema."""
        return UserResponse.model_validate(user)
