import uuid

from sqlalchemy import Enum, String, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base
from models.enums import ExchangeType


class WatchedSymbol(Base):
    __tablename__ = "watched_symbols"

    __table_args__ = (
        UniqueConstraint("symbol", "exchange", name="uq_watched_symbol_exchange"),
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    exchange: Mapped[ExchangeType] = mapped_column(Enum(ExchangeType), nullable=False)

    def __repr__(self):
        return f"<WatchedSymbol {self.symbol} @ {self.exchange.value}>"
