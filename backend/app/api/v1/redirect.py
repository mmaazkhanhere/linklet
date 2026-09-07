from backend.app.core.database import get_db
from backend.app.services.link_service import LinkService
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}", status_code=307)
async def redirect_short_code(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    link_service: LinkService = Depends(),
) -> RedirectResponse:
    destination_url = await link_service.resolve_and_record_click(db, short_code)
    return RedirectResponse(url=destination_url, status_code=307)
