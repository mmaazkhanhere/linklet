from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Uuid, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (
        CheckConstraint("total_clicks >= 0", name="chk_links_total_clicks_non_negative"),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="RESTRICT", name="fk_links_user"), nullable=False, index=True)
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    short_code: Mapped[str] = mapped_column(String(7), unique=True, index=True, nullable=False)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    user = relationship("User", back_populates="links")
