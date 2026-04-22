"""
psx_client.py — importable PSX stock data fetcher.
No CLI. Use PSXClient directly in your Flask routes.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import os
import sqlite3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/db.db")

def load_unique_symbols_from_db() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT symbol FROM transactions")
    rows = cur.fetchall()

    conn.close()
    return [r[0] for r in rows]

BASE_URL = "https://psxterminal.com/api/ticks/REG"
DEFAULT_PAGE_SIZE = 10
MAX_WORKERS = 3
REQUEST_TIMEOUT = 10
CACHE_TTL_SECONDS = 60


@dataclass
class StockTick:
    symbol: str
    data: dict[str, Any]
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @classmethod
    def from_response(cls, symbol: str, payload: dict) -> "StockTick":
        data = payload.get("data")
        if data is None:
            raise ValueError(f"Missing 'data' key in response for {symbol}")
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


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class PSXClient:
    def __init__(
        self,
        symbols: list[str] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_workers: int = MAX_WORKERS,
        timeout: int = REQUEST_TIMEOUT,
        cache_ttl: int = CACHE_TTL_SECONDS,
    ) -> None:
        self.symbols = symbols or []
        self.page_size = page_size
        self.max_workers = max_workers
        self.timeout = timeout
        self._session = _build_session()
        self._cache = _Cache(ttl_seconds=cache_ttl)

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
            "stocks": [ { "symbol": "...", "data": {...}, "fetched_at": "..." }, ... ]
        }
        """
        if page < 1:
            raise ValueError(f"page must be >= 1, got {page}")

        total = len(self.symbols)
        total_pages = (total + self.page_size - 1) // self.page_size

        if page > total_pages:
            raise ValueError(f"page {page} exceeds total_pages {total_pages}")

        start = (page - 1) * self.page_size
        slice_ = self.symbols[start : start + self.page_size]
        items = self._fetch_many(slice_)

        return {
            "page": page,
            "page_size": self.page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "stocks": [t.to_dict() for t in items],
        }

    def get_all(self) -> dict:
        """
        Fetches all symbols in one shot (no pagination).
        Returns:
        {
            "total": 51,
            "stocks": [ { "symbol": "...", "fetched_at": "...", ... }, ... ]
        }
        """
        items = self._fetch_many(self.symbols)
        return {
            "total": len(items),
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

        url = f"{BASE_URL}/{symbol}"
        resp = self._session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        tick = StockTick.from_response(symbol, resp.json())
        self._cache.set(tick)
        return tick

    def _fetch_many(self, symbols: list[str]) -> list[StockTick]:
        results: dict[str, StockTick] = {}
        to_fetch = []

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
                "Fetched %d symbols in %.2fs",
                len(to_fetch),
                time.perf_counter() - start,
            )

        return [results[sym] for sym in symbols if sym in results]


# Module-level singleton — import and use directly in your routes
symbols = load_unique_symbols_from_db()
psx = PSXClient(symbols=symbols)