from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.link import LinkCreate, LinkListResponse, LinkResponse
from backend.app.services.link_service import LinkService

router = APIRouter(prefix="/links", tags=["links"])


@router.get("", response_model=LinkListResponse)
async def list_links(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    link_service: LinkService = Depends(),
) -> LinkListResponse:
    return await link_service.list_links(db, current_user)


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    request: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    link_service: LinkService = Depends(),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=255),
) -> LinkResponse:
    return await link_service.create_link(db, current_user, request, idempotency_key)
