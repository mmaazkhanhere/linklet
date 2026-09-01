from pydantic import BaseModel


class IdempotencyRecord(BaseModel):
    idempotency_key: str
    request_path: str
    response_code: int | None = None
    response_body: dict | None = None

    class Config:
        from_attributes = True
