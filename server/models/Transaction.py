import enum
from datetime import date
from db.database import Base
from models.mixins.TimestampMixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Date, ForeignKey, Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Portfolio import Portfolio

class Side(enum.Enum):
    SELL = "SELL"
    BUY = "BUY"


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    portfolio_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("portfolios.id"), nullable=False, index=True
    )

    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio", back_populates="transactions"
    )

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    sector: Mapped[str] = mapped_column(String(150))

    side: Mapped[Side] = mapped_column(Enum(Side), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    rate: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    taxes: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    charges: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.symbol} - {self.total_amount} on {self.transaction_date}>"
