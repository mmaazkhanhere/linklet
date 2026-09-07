from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.exceptions import InvalidTokenError
from backend.app.core.security import decode_access_token
from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts Bearer token, decodes JWT,
    fetches User entity from repository, and returns User instance.
    Raises InvalidTokenError (401 Unauthorized) if token is missing/expired/corrupted or user non-existent.
    """
    if not token:
        raise InvalidTokenError("Missing authentication token.")

    try:
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Token payload missing sub claim.")
    except jwt.PyJWTError:
        raise InvalidTokenError("Invalid or expired authentication token.")

    user_repo = UserRepository()
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise InvalidTokenError("Authenticated user no longer exists.")

    return user
