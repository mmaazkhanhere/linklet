from fastapi import APIRouter
from backend.app.api.v1 import auth, links, redirect

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(links.router)
api_router.include_router(redirect.router)
