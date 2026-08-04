import enum
import uuid
from db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Enum, event, UUID
from typing import TYPE_CHECKING
from .enums import ExchangeType

if TYPE_CHECKING:
    from ..features.auth.models.User import User
    from .Transaction import Transaction


class Portfolio(Base):
    __tablename__ = "portfolios"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "mysql"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    exchange: Mapped[ExchangeType] = mapped_column(Enum(ExchangeType), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Portfolio {self.name}>"


@event.listens_for(Portfolio.exchange, "set")
def receive_set(target, value, oldvalue, initiator):
    currency_map = {
        ExchangeType.PSX: "PKR",
        ExchangeType.TADAWUL: "SAR",
        ExchangeType.US: "USD",
    }
    target.currency = currency_map.get(value, "USD")
