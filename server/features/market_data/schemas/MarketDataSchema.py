from datetime import datetime
from typing import Optional

from features.base.schema import BaseSchema

# ─── /data/status ───────────────────────────────────────────

class DataStatusResponse(BaseSchema):
    stored_csv_counts: dict[str, int]


# ─── /exchanges ─────────────────────────────────────────────

class ExchangeInfo(BaseSchema):
    folder: str
    suffix: str
    ticker_count: int
    tickers: list[str]


ExchangesResponse = dict[str, ExchangeInfo]


# ─── /data/{exchange}/{ticker} ──────────────────────────────

class OHLCVRow(BaseSchema):
    date: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class TickerDataResponse(BaseSchema):
    exchange: str
    ticker: str
    rows: int
    data: list[OHLCVRow]


# ─── /tickers/reload ────────────────────────────────────────

# Returns e.g. {"PSX": 42, "US": 100, "SAUDI": 55}
TickersReloadResponse = dict[str, int]
