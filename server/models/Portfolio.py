import enum
from db.database import Base
from models.mixins.TimestampMixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Enum, event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .User import User
    from .Transaction import Transaction


class ExchangeType(enum.Enum):
    PSX = "PSX"
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    TADAWUL = "TADAWUL"


class Portfolio(TimestampMixin, Base):
    __tablename__ = "portfolios"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    exchange: Mapped[ExchangeType] = mapped_column(Enum(ExchangeType), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255))

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
        ExchangeType.NASDAQ: "USD",
        ExchangeType.NYSE: "USD",
    }
    target.currency = currency_map.get(value, "USD")
