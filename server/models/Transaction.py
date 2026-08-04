import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import Numeric
from db.database import Base
from models.model_enums.side import Side
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Date, ForeignKey, Enum, UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Portfolio import Portfolio


class Transaction(Base):
    __tablename__ = "transactions"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "mysql"),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio", back_populates="transactions"
    )

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    sector: Mapped[str] = mapped_column(String(150), nullable=True)
    side: Mapped[Side] = mapped_column(Enum(Side), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    taxes: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.symbol} - {self.total_amount}>"
