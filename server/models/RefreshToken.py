from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime, UUID, Boolean
from models.mixins.TimestampMixin import TimestampMixin
from datetime import datetime, UTC
import uuid
from db.database import Base


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(
        String(512), nullable=False, unique=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "mysql"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at.replace(tzinfo=UTC)
