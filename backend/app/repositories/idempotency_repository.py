from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.idempotency import IdempotencyRequest


class IdempotencyRepository:
    async def get_for_update(
        self, db: AsyncSession, user_id: str, operation: str, key: str
    ) -> IdempotencyRequest | None:
        result = await db.execute(
            select(IdempotencyRequest)
            .where(
                IdempotencyRequest.user_id == user_id,
                IdempotencyRequest.operation == operation,
                IdempotencyRequest.idempotency_key == key,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def insert_processing(
        self,
        db: AsyncSession,
        record: IdempotencyRequest,
    ) -> bool:
        """Insert a claim, returning False when another transaction owns the key."""
        try:
            async with db.begin_nested():
                db.add(record)
                await db.flush()
            return True
        except IntegrityError:
            return False

    async def complete(
        self, record: IdempotencyRequest, response_code: int, response_body: str, now: datetime
    ) -> None:
        record.status = "COMPLETED"
        record.response_code = response_code
        record.response_body = response_body
        record.updated_at = now
        # Flush the completion before the enclosing business transaction commits.
        # This guarantees that a subsequent request can observe COMPLETED rather
        # than incorrectly treating the key as still in progress.

    async def fail(self, record: IdempotencyRequest, response_body: str | None, now: datetime) -> None:
        record.status = "FAILED"
        record.response_body = response_body
        record.updated_at = now
