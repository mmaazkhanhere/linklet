from fastapi import APIRouter

router = APIRouter(prefix="/links", tags=["links"])


@router.get("")
async def list_links():
    return {"items": [], "total": 0}
