from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Uuid, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base


class IdempotencyRequest(Base):
    __tablename__ = "idempotency_request"
    __table_args__ = (
        CheckConstraint("status IN ('PROCESSING', 'COMPLETED', 'FAILED')", name="chk_idempotency_status"),
        CheckConstraint("operation IN ('CREATE', 'DELETE', 'REGENERATE')", name="chk_idempotency_operation"),
        Index("idx_idempotency_expires_at", "expires_at"),
    )

    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE", name="fk_idempotency_user"), primary_key=True)
    operation: Mapped[str] = mapped_column(String(16), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
