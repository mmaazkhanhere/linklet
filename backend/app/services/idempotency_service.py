import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import IdempotencyInProgressError, IdempotencyKeyMisuseError
from backend.app.models.idempotency import IdempotencyRequest


def request_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotencyService:
    async def claim(self, db: AsyncSession, user_id: str, operation: str, key: str, payload: dict):
        digest = request_hash(payload)
        now = datetime.now(timezone.utc)
        existing = await db.scalar(select(IdempotencyRequest).where(
            IdempotencyRequest.user_id == user_id,
            IdempotencyRequest.operation == operation,
            IdempotencyRequest.idempotency_key == key,
        ).with_for_update())
        if existing:
            if existing.request_hash != digest:
                raise IdempotencyKeyMisuseError()
            if existing.status == "COMPLETED":
                return existing, json.loads(existing.response_body)
            if existing.status == "PROCESSING" and (now - existing.updated_at).total_seconds() <= 30:
                raise IdempotencyInProgressError()
            existing.status = "PROCESSING"
            existing.updated_at = now
            existing.expires_at = now + timedelta(hours=24)
            return existing, None

        record = IdempotencyRequest(
            user_id=user_id, operation=operation, idempotency_key=key,
            request_hash=digest, status="PROCESSING", created_at=now,
            updated_at=now, expires_at=now + timedelta(hours=24),
        )
        db.add(record)
        await db.flush()
        return record, None

    async def complete(self, record: IdempotencyRequest, response_code: int, body: dict):
        record.status = "COMPLETED"
        record.response_code = response_code
        record.response_body = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        record.updated_at = datetime.now(timezone.utc)
