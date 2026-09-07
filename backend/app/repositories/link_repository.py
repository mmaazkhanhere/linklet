from backend.app.models.link import Link
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class LinkRepository:
    async def list_by_user(self, db: AsyncSession, user_id: str) -> list[Link]:
        result = await db.execute(
            select(Link).where(Link.user_id == user_id).order_by(Link.created_on.desc())
        )
        return list(result.scalars().all())

    async def get_by_short_code(self, db: AsyncSession, short_code: str) -> Link | None:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        return result.scalar_one_or_none()

    async def increment_clicks_and_get_destination(
        self, db: AsyncSession, short_code: str
    ) -> str | None:
        result = await db.execute(
            update(Link)
            .where(Link.short_code == short_code)
            .values(total_clicks=Link.total_clicks + 1)
            .returning(Link.destination_url)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        user_id: str,
        destination_url: str,
        short_code: str,
    ) -> Link:
        link = Link(user_id=user_id, destination_url=destination_url, short_code=short_code)
        db.add(link)
        await db.flush()
        return link
