from datetime import datetime
from pydantic import BaseModel, HttpUrl


class LinkCreate(BaseModel):
    target_url: str


class LinkResponse(BaseModel):
    id: str
    target_url: str
    short_code: str
    short_url: str
    clicks: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    total: int
