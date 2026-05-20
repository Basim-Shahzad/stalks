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


class HoldingSchema(Base):
    symbol: str
    quantity: float
    avg_buy_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_profit: Decimal
    unrealized_pct: Decimal

    model_config = {"from_attributes": True}


class PortfolioStatsSchema(Base):
    # Capital
    total_invested: Decimal
    portfolio_value: Decimal

    # Costs
    total_costs: Decimal

    # P&L
    realized_profit: Decimal
    unrealized_profit: Decimal
    total_profit: Decimal
    total_return_pct: Decimal

    # Per-symbol breakdown
    holdings: list[HoldingSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}
