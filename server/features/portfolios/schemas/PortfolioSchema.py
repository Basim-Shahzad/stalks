import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from features.base.schema import BaseSchema
from models.enums import ExchangeType
from features.portfolios.models.Portfolio import Broker


class PortfolioSchema(BaseSchema):
    id: uuid.UUID
    exchange: ExchangeType
    currency: str
    name: str
    description: str
    broker: Broker | None = None
    created_at: datetime
    updated_at: datetime


class PortfolioListItemSchema(BaseSchema):
    id: uuid.UUID
    exchange: ExchangeType
    currency: str
    name: str
    description: str
    broker: Broker | None = None
    created_at: datetime
    updated_at: datetime


class PortfolioCreateSchema(BaseSchema):
    exchange: ExchangeType = ExchangeType.PSX
    currency: str = "PKR"
    name: str
    description: str
    broker: Broker | None = None


class PortfolioUpdateSchema(PortfolioCreateSchema):
    pass


class PortfolioHoldings(BaseSchema):
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
    has_market_data: bool = False
    market_data_stale: bool = False
    quote_fetched_at: datetime | None = None
    realised_pnl: Decimal = Field(default=Decimal("0"))
    market_value: Decimal = Field(default=Decimal("0"))
    cost_basis: Decimal = Field(default=Decimal("0"))
    unrealised_pnl: Decimal = Field(default=Decimal("0"))
    unrealised_pnl_pct: Decimal = Field(default=Decimal("0"))
    total_pnl: Decimal = Field(default=Decimal("0"))


class PortfolioSummary(BaseSchema):
    total_invested: Decimal
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_fees: Decimal
    total_unrealised_pnl: Decimal
    total_realised_pnl: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    holdings_count: int
    holdings_with_market_data: int


class PortfolioHoldingsResponse(BaseSchema):
    holdings: list[PortfolioHoldings]
    summary: PortfolioSummary
