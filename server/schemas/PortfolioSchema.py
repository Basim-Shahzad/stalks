import enum
from datetime import datetime
from decimal import Decimal
import uuid
from .base import Base
from models.enums import ExchangeType
from pydantic import Field


class PortfolioSchema(Base):

    id: uuid.UUID
    exchange: ExchangeType
    currency: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioListItemSchema(Base):

    id: uuid.UUID
    exchange: ExchangeType
    currency: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioCreateSchema(Base):

    exchange: ExchangeType = ExchangeType.US
    currency: str = "USD"
    name: str
    description: str

    class Config:
        from_attributes = True


class PortfolioUpdateSchema(PortfolioCreateSchema):
    pass


class PortfolioHoldings(Base):
    symbol: str
    company: str
    sector: str
    quantity: Decimal
    avg_cost: Decimal
    total_invested: Decimal
    total_fees: Decimal
    current_price: Decimal = Decimal("0")
    ldcp: Decimal = Decimal("0")
    day_change: Decimal = Decimal("0")
    day_change_pct: Decimal = Decimal("0")
    direction: str = ""
    realised_pnl: Decimal = Field(default=Decimal("0"))
    market_value: Decimal = Field(default=Decimal("0"))
    cost_basis: Decimal = Field(default=Decimal("0"))
    unrealised_pnl: Decimal = Field(default=Decimal("0"))
    unrealised_pnl_pct: Decimal = Field(default=Decimal("0"))
    total_pnl: Decimal = Field(default=Decimal("0"))


class PortfolioSummary(Base):
    total_invested: Decimal
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_fees: Decimal
    total_unrealised_pnl: Decimal
    total_realised_pnl: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    holdings_count: int


class PortfolioHoldingsResponse(Base):
    holdings: list[PortfolioHoldings]
    summary: PortfolioSummary
