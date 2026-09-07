from backend.app.models.link import Link
from sqlalchemy import delete, select, update
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

    async def get_owned_for_update(
        self, db: AsyncSession, link_id: str, user_id: str
    ) -> Link | None:
        result = await db.execute(
            select(Link)
            .where(Link.id == link_id, Link.user_id == user_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def update_short_code(self, db: AsyncSession, link: Link, short_code: str) -> Link:
        link.short_code = short_code
        await db.flush()
        return link

    async def delete_owned(self, db: AsyncSession, link_id: str, user_id: str) -> bool:
        result = await db.execute(
            delete(Link).where(Link.id == link_id, Link.user_id == user_id)
        )
        await db.flush()
        return result.rowcount == 1

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
