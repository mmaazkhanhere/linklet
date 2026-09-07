from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.user import User


class UserRepository:
    """Repository handling persistence and lookup for User entities."""

    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Fetch user by primary key ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, email_address: str) -> Optional[User]:
        """Fetch user by unique email address."""
        result = await db.execute(select(User).where(User.email_address == email_address.lower().strip()))
        return result.scalars().first()

    async def create(self, db: AsyncSession, name: str, email_address: str, password_hash: str) -> User:
        """Create and persist a new User entity."""
        user = User(
            name=name.strip(),
            email_address=email_address.lower().strip(),
            hashed_password=password_hash,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
