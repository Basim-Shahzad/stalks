from db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from features.portfolios.models.Portfolio import Portfolio


class User(Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, unique=True
    )
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    portfolios: Mapped[list["Portfolio"]] = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.name}>"
