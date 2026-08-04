from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .base import Base

# ─── /data/status ───────────────────────────────────────────

class FetchResult(Base):
    exchange: str
    total: int
    success: int
    failed: int


class DataStatusResponse(Base):
    fetch_running: bool
    last_fetch_result: Optional[list[FetchResult]] = None
    next_scheduled_run: Optional[str] = None
    stored_csv_counts: dict[str, int]


# ─── /exchanges ─────────────────────────────────────────────

class ExchangeInfo(Base):
    folder: str
    suffix: str
    ticker_count: int
    tickers: list[str]


ExchangesResponse = dict[str, ExchangeInfo]


# ─── /fetch/initial  &  /fetch/incremental ──────────────────

class FetchTriggerResponse(Base):
    message: str
    exchange: str


# ─── /data/{exchange}/{ticker} ──────────────────────────────

class OHLCVRow(Base):
    date: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class TickerDataResponse(Base):
    exchange: str
    ticker: str
    rows: int
    data: list[OHLCVRow]


# ─── /tickers/reload ────────────────────────────────────────

# Returns e.g. {"PSX": 42, "US": 100, "SAUDI": 55}
TickersReloadResponse = dict[str, int]