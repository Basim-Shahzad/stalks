from datetime import date, datetime
from app import db
from .mixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy import String, Integer, Numeric, Date

class Transaction(TimestampMixin, db.Model):
    __tablename__ = "transactions"

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    sector: Mapped[str] = mapped_column(String(100))

    buy: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0)
    sell: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0)
    rate: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    taxes: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    charges: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.symbol} - {self.total_amount}>"
    
    def to_dict(self):
        return {
            # Fields from TimestampMixin
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            
            # Fields from Transaction
            "date": self.transaction_date.isoformat() if self.transaction_date else None,
            "company": self.company,
            "symbol": self.symbol,
            "sector": self.sector,
            "buy": float(self.buy),
            "sell": float(self.sell),
            "rate": float(self.rate),
            "commission": float(self.commission),
            "taxes": float(self.taxes),
            "charges": float(self.charges),
            "total_amount": float(self.total_amount)
        }