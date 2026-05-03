from datetime import date, datetime
from app import db
from .data.mixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    portfolios: Mapped[list["Portfolio"]] = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Portfolio(TimestampMixin, db.Model):
    __tablename__ = "portfolios"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="portfolios")

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255))

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="portfolio", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Portfolio {self.name}>"


class Transaction(TimestampMixin, db.Model):
    __tablename__ = "transactions"

    portfolio_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("portfolios.id"), nullable=False
    )

    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio", back_populates="transactions"
    )

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

    @property
    def total_fees(self):
        """Sums up all the extra costs."""
        return float(self.commission + self.taxes + self.charges)
    
    def __repr__(self):
        return f"<Transaction {self.symbol} - {self.total_amount}>"
    


    def to_dict(self):
        return {
            "id": self.id,
            "date": (
                self.transaction_date.isoformat() if self.transaction_date else None
            ),
            "company": self.company,
            "symbol": self.symbol,
            "sector": self.sector,
            "buy": float(self.buy),
            "sell": float(self.sell),
            "rate": float(self.rate),
            "commission": float(self.commission),
            "taxes": float(self.taxes),
            "charges": float(self.charges),
            "total_amount": float(self.total_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class TokenBlocklist(TimestampMixin, db.Model):
    __tablename__ = "token_blocklist"

    jti: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)