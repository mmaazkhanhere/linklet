from fastapi import APIRouter

router = APIRouter(tags=["redirect"])


@router.get("/r/{short_code}")
async def redirect_short_code(short_code: str):
    return {"short_code": short_code, "status": "redirect placeholder"}
