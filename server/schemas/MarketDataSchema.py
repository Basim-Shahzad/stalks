from pydantic import BaseModel
from typing import Any, Optional


# ─── /data/status ───────────────────────────────────────────

class FetchResult(BaseModel):
    exchange: str
    total: int
    success: int
    failed: int


class DataStatusResponse(BaseModel):
    fetch_running: bool
    last_fetch_result: Optional[list[FetchResult]] = None
    next_scheduled_run: Optional[str] = None
    stored_csv_counts: dict[str, int]


# ─── /exchanges ─────────────────────────────────────────────

class ExchangeInfo(BaseModel):
    folder: str
    suffix: str
    ticker_count: int
    tickers: list[str]


ExchangesResponse = dict[str, ExchangeInfo]


# ─── /fetch/initial  &  /fetch/incremental ──────────────────

class FetchTriggerResponse(BaseModel):
    message: str
    exchange: str


# ─── /data/{exchange}/{ticker} ──────────────────────────────

class OHLCVRow(BaseModel):
    Date: str
    Open: Optional[float] = None
    High: Optional[float] = None
    Low: Optional[float] = None
    Close: Optional[float] = None
    Volume: Optional[float] = None


class TickerDataResponse(BaseModel):
    exchange: str
    ticker: str
    rows: int
    data: list[OHLCVRow]


# ─── /tickers/reload ────────────────────────────────────────

# Returns e.g. {"PSX": 42, "US": 100, "SAUDI": 55}
TickersReloadResponse = dict[str, int]