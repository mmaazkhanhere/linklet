from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LinkCreate(BaseModel):
    destination_url: str = Field(min_length=1)


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    link_id: str
    destination_url: str
    short_code: str
    total_clicks: int
    created_on: datetime


class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    total: int
