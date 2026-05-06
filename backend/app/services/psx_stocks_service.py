"""
psx_client.py — importable stock data fetcher using yfinance.
No CLI. Use PSXClient directly in your Flask routes.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import os
import sqlite3
import yfinance as yf

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/db.db")

DEFAULT_PAGE_SIZE = 10
MAX_WORKERS = 3
CACHE_TTL_SECONDS = 60


def load_unique_symbols_from_db() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM transactions")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


@dataclass
class StockTick:
    symbol: str
    data: dict[str, Any]
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @classmethod
    def from_yfinance(cls, symbol: str) -> "StockTick":
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info  # lightweight — no full metadata fetch

        # Map yfinance fast_info fields to a flat dict similar to the old PSX payload
        data = {
            "last_price":        getattr(info, "last_price", None),
            "previous_close":    getattr(info, "previous_close", None),
            "open":              getattr(info, "open", None),
            "day_high":          getattr(info, "day_high", None),
            "day_low":           getattr(info, "day_low", None),
            "volume":            getattr(info, "last_volume", None),
            "market_cap":        getattr(info, "market_cap", None),
            "fifty_day_average": getattr(info, "fifty_day_average", None),
            "two_hundred_day_average": getattr(info, "two_hundred_day_average", None),
            "currency":          getattr(info, "currency", None),
            "exchange":          getattr(info, "exchange", None),
        }

        # Compute simple change / change-percent from available fields
        last  = data["last_price"]
        prev  = data["previous_close"]
        if last is not None and prev is not None and prev != 0:
            data["change"]         = round(last - prev, 4)
            data["change_percent"] = round((last - prev) / prev * 100, 4)
        else:
            data["change"]         = None
            data["change_percent"] = None

        return cls(symbol=symbol, data=data)

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "fetched_at": self.fetched_at, **self.data}


class _Cache:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self._store: dict[str, tuple[StockTick, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, symbol: str) -> Optional[StockTick]:
        entry = self._store.get(symbol)
        if entry and datetime.utcnow() - entry[1] < self._ttl:
            return entry[0]
        return None

    def set(self, tick: StockTick) -> None:
        self._store[tick.symbol] = (tick, datetime.utcnow())

    def invalidate(self, symbol: Optional[str] = None) -> None:
        if symbol:
            self._store.pop(symbol, None)
        else:
            self._store.clear()


class PSXClient:
    def __init__(
        self,
        symbols: list[str] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_workers: int = MAX_WORKERS,
        cache_ttl: int = CACHE_TTL_SECONDS,
    ) -> None:
        self.symbols   = symbols or []
        self.page_size = page_size
        self.max_workers = max_workers
        self._cache    = _Cache(ttl_seconds=cache_ttl)

    # ------------------------------------------------------------------ #
    # Public API (same contract as before)                                 #
    # ------------------------------------------------------------------ #

    def get_page(self, page: int = 1) -> dict:
        """
        Returns a JSON-serialisable dict ready for jsonify():
        {
            "page": 1,
            "page_size": 10,
            "total": 51,
            "total_pages": 6,
            "has_next": true,
            "has_prev": false,
            "stocks": [ { "symbol": "...", ... }, ... ]
        }
        """
        if page < 1:
            raise ValueError(f"page must be >= 1, got {page}")

        total       = len(self.symbols)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)

        if page > total_pages:
            raise ValueError(f"page {page} exceeds total_pages {total_pages}")

        start  = (page - 1) * self.page_size
        slice_ = self.symbols[start : start + self.page_size]
        items  = self._fetch_many(slice_)

        return {
            "page":        page,
            "page_size":   self.page_size,
            "total":       total,
            "total_pages": total_pages,
            "has_next":    page < total_pages,
            "has_prev":    page > 1,
            "stocks":      [t.to_dict() for t in items],
        }

    def get_all(self) -> dict:
        """Fetches all symbols in one shot (no pagination)."""
        items = self._fetch_many(self.symbols)
        return {
            "total":  len(items),
            "stocks": [t.to_dict() for t in items],
        }

    def get_symbol(self, symbol: str) -> dict:
        """Returns a single stock tick as a JSON-serialisable dict."""
        return self._fetch_one(symbol.upper()).to_dict()

    def invalidate_cache(self, symbol: Optional[str] = None) -> None:
        self._cache.invalidate(symbol)

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _fetch_one(self, symbol: str) -> StockTick:
        cached = self._cache.get(symbol)
        if cached:
            return cached

        tick = StockTick.from_yfinance(symbol)
        self._cache.set(tick)
        return tick

    def _fetch_many(self, symbols: list[str]) -> list[StockTick]:
        results: dict[str, StockTick] = {}
        to_fetch: list[str] = []

        for sym in symbols:
            cached = self._cache.get(sym)
            if cached:
                results[sym] = cached
            else:
                to_fetch.append(sym)

        if to_fetch:
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = {pool.submit(self._fetch_one, sym): sym for sym in to_fetch}
                for future in as_completed(futures):
                    sym = futures[future]
                    try:
                        results[sym] = future.result()
                    except Exception as exc:
                        logger.warning("Skipping %s: %s", sym, exc)
            logger.info(
                "Fetched %d symbols via yfinance in %.2fs",
                len(to_fetch),
                time.perf_counter() - start,
            )

        return [results[sym] for sym in symbols if sym in results]


# Module-level singleton — import and use directly in your routes
symbols = load_unique_symbols_from_db()
psx = PSXClient(symbols=symbols)