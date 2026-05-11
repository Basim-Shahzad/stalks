from db.database import Base
from models.mixins.TimestampMixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class TokenBlocklist(TimestampMixin, Base):
    __tablename__ = "token_blocklist"

    jti: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
