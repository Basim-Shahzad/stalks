from datetime import date

from features.base.schema import BaseSchema


class OHLCVBar(BaseSchema):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataResponse(BaseSchema):
    exchange: str
    symbol: str
    rows: int
    data: list[OHLCVBar]
