from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.models.user import User
from backend.app.repositories.link_repository import LinkRepository
from backend.app.schemas.link import LinkCreate, LinkListResponse, LinkResponse
from backend.app.services.generator_service import generate_short_code


class LinkService:
    def __init__(self):
        self.link_repo = LinkRepository()

    async def list_links(self, db: AsyncSession, user: User) -> LinkListResponse:
        links = await self.link_repo.list_by_user(db, user.id)
        items = [self._to_response(link) for link in links]
        return LinkListResponse(items=items, total=len(items))

    async def create_link(self, db: AsyncSession, user: User, request: LinkCreate) -> LinkResponse:
        short_code = await self._generate_unique_short_code(db)
        link = await self.link_repo.create(
            db=db,
            user_id=user.id,
            target_url=request.target_url,
            short_code=short_code,
        )
        return self._to_response(link)

    async def _generate_unique_short_code(self, db: AsyncSession) -> str:
        for _ in range(10):
            short_code = generate_short_code()
            existing_link = await self.link_repo.get_by_short_code(db, short_code)
            if existing_link is None:
                return short_code
        return generate_short_code(10)

    @staticmethod
    def _to_response(link) -> LinkResponse:
        return LinkResponse(
            id=link.id,
            target_url=link.target_url,
            short_code=link.short_code,
            short_url=f"{settings.BASE_URL}/r/{link.short_code}",
            clicks=link.clicks,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )
