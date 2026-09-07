from backend.app.core.exceptions import (
    InvalidDestinationUrlError,
    LinkNotFoundError,
    ShortCodeGenerationFailedError,
)
from backend.app.models.user import User
from backend.app.repositories.link_repository import LinkRepository
from backend.app.schemas.link import LinkCreate, LinkDeleteResponse, LinkResponse
from backend.app.services.generator_service import generate_short_code
from backend.app.services.idempotency_service import IdempotencyService
from backend.app.services.url_validator import validate_destination_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class LinkService:
    def __init__(self):
        self.link_repo = LinkRepository()
        self.idempotency = IdempotencyService()

    async def list_links(self, db: AsyncSession, user: User) -> list[LinkResponse]:
        links = await self.link_repo.list_by_user(db, user.id)
        return [self._to_response(link) for link in links]

    async def regenerate_link(
        self, db: AsyncSession, user: User, link_id: str, idempotency_key: str | None = None
    ) -> LinkResponse:
        user_id = user.id
        if db.in_transaction():
            await db.rollback()
        async with db.begin():
            record = None
            if idempotency_key:
                record, replay = await self.idempotency.claim(
                    db, user_id, "REGENERATE", idempotency_key, {"link_id": link_id}
                )
                if replay is not None:
                    return LinkResponse.model_validate(replay)

            link = await self.link_repo.get_owned_for_update(db, link_id, user_id)
            if link is None:
                raise LinkNotFoundError()
            old_code = link.short_code
            for _ in range(5):
                candidate = generate_short_code()
                if candidate == old_code:
                    continue
                try:
                    async with db.begin_nested():
                        await self.link_repo.update_short_code(db, link, candidate)
                    break
                except IntegrityError as exc:
                    message = str(exc).lower()
                    if "short_code" not in message and "ix_links_short_code" not in message:
                        raise
            else:
                raise ShortCodeGenerationFailedError()

            response = self._to_response(link)
            if record:
                await self.idempotency.complete(record, 200, response.model_dump(mode="json"))
            return response

    async def delete_link(
        self, db: AsyncSession, user: User, link_id: str, idempotency_key: str | None = None
    ) -> LinkDeleteResponse:
        user_id = user.id
        if db.in_transaction():
            await db.rollback()
        async with db.begin():
            record = None
            if idempotency_key:
                record, replay = await self.idempotency.claim(
                    db, user_id, "DELETE", idempotency_key, {"link_id": link_id}
                )
                if replay is not None:
                    return LinkDeleteResponse.model_validate(replay)

            link = await self.link_repo.get_owned_for_update(db, link_id, user_id)
            if link is None:
                raise LinkNotFoundError()
            deleted = await self.link_repo.delete_owned(db, link_id, user_id)
            if not deleted:
                raise LinkNotFoundError()

            response = LinkDeleteResponse(message="Link successfully deleted.")
            if record:
                await self.idempotency.complete(record, 200, response.model_dump(mode="json"))
            return response

    async def resolve_and_record_click(self, db: AsyncSession, short_code: str) -> str:
        destination_url = await self.link_repo.increment_clicks_and_get_destination(db, short_code)
        if destination_url is None:
            await db.rollback()
            raise LinkNotFoundError()
        await db.commit()
        return destination_url

    async def create_link(
        self, db: AsyncSession, user: User, request: LinkCreate, idempotency_key: str | None = None
    ) -> LinkResponse:
        try:
            validate_destination_url(request.destination_url)
        except ValueError as exc:
            raise InvalidDestinationUrlError() from exc
        user_id = user.id
        if db.in_transaction():
            await db.rollback()
        async with db.begin():
            record = None
            if idempotency_key:
                record, replay = await self.idempotency.claim(
                    db, user_id, "CREATE", idempotency_key, request.model_dump()
                )
                if replay is not None:
                    return LinkResponse.model_validate(replay)

            link = None
            for _ in range(5):
                try:
                    async with db.begin_nested():
                        link = await self.link_repo.create(
                            db=db, user_id=user_id,
                            destination_url=request.destination_url,
                            short_code=generate_short_code(),
                        )
                    break
                except IntegrityError as exc:
                    message = str(exc).lower()
                    if "short_code" not in message and "ix_links_short_code" not in message:
                        raise
            if link is None:
                raise ShortCodeGenerationFailedError()

            response = self._to_response(link)
            if record:
                await self.idempotency.complete(record, 201, response.model_dump(mode="json"))
            return response

    @staticmethod
    def _to_response(link) -> LinkResponse:
        return LinkResponse(
            link_id=link.id,
            destination_url=link.destination_url,
            short_code=link.short_code,
            total_clicks=link.total_clicks,
            created_on=link.created_on,
        )
