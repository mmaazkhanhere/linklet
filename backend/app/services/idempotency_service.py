import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import IdempotencyInProgressError, IdempotencyKeyMisuseError
from backend.app.models.idempotency import IdempotencyRequest
from backend.app.repositories.idempotency_repository import IdempotencyRepository


def request_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def empty_request_hash() -> str:
    return hashlib.sha256(b"").hexdigest()


class IdempotencyService:
    def __init__(self):
        self.repository = IdempotencyRepository()

    async def claim(
        self, db: AsyncSession, user_id: str, operation: str, key: str, payload: dict | None
    ):
        digest = request_hash(payload) if payload is not None else empty_request_hash()
        now = datetime.now(timezone.utc)
        record = IdempotencyRequest(
            user_id=user_id, operation=operation, idempotency_key=key,
            request_hash=digest, status="PROCESSING", created_at=now,
            updated_at=now, expires_at=now + timedelta(hours=24),
        )
        inserted = await self.repository.insert_processing(db, record)
        if inserted:
            return record, None
        existing = await self.repository.get_for_update(db, user_id, operation, key)
        if existing:
            if existing.request_hash != digest:
                raise IdempotencyKeyMisuseError()
            if existing.status == "COMPLETED":
                return existing, json.loads(existing.response_body or "null")
            updated_at = existing.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            if existing.status == "PROCESSING" and (now - updated_at).total_seconds() <= 30:
                raise IdempotencyInProgressError()
            existing.status = "PROCESSING"
            existing.updated_at = now
            existing.expires_at = now + timedelta(hours=24)
            return existing, None

        raise RuntimeError("idempotency claim disappeared after a uniqueness conflict")

    async def complete(self, db: AsyncSession, record: IdempotencyRequest, response_code: int, body: dict):
        await self.repository.complete(
            record,
            response_code,
            json.dumps(body, separators=(",", ":"), ensure_ascii=False),
            datetime.now(timezone.utc),
        )
        await db.flush()

    async def fail(self, db: AsyncSession, record: IdempotencyRequest, body: dict | None = None):
        await self.repository.fail(
            record,
            json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body is not None else None,
            datetime.now(timezone.utc),
        )
        await db.flush()
