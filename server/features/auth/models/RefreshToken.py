from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime, UUID, Boolean
from datetime import datetime, UTC
import uuid
from db.database import Base


class RefreshToken(Base):
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
        expires_at = self.expires_at
        if expires_at.tzinfo is None:  # some backends return naive UTC
            expires_at = expires_at.replace(tzinfo=UTC)
        return datetime.now(UTC) > expires_at
