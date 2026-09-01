from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me():
    return {"message": "Auth endpoint active"}
