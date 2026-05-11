from db.database import Base
from models.mixins.TimestampMixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey
from Portfolio import Portfolio


class User(TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    portfolios: Mapped[list["Portfolio"]] = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self):
        return f"<User {self.username}>"
