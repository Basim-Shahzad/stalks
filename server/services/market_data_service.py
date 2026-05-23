import time
from datetime import date, timedelta
from core.logger import logger
import threading
from typing import Optional

import pandas as pd
import yfinance as yf

from dependencies.market_data.config import (
    BATCH_DELAY_SECONDS,
    BATCH_SIZE,
    EXCHANGES,
    INITIAL_PERIOD,
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
)
from dependencies.market_data.data_store import get_last_date, save

_shutdown_event = threading.Event()

# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────


def stop_background_fetch() -> None:
    """Signal any running fetch to stop after its current ticker."""
    _shutdown_event.set()


def _yf_symbol(exchange_key: str, base_ticker: str) -> str:
    """Append the exchange suffix to produce a yfinance-compatible symbol."""
    return base_ticker + EXCHANGES[exchange_key]["suffix"]


def _fetch_single(
    yf_symbol: str, start: str | None = None, period: str | None = None
) -> pd.DataFrame | None:
    """
    Download OHLCV data for one symbol.
    Retries up to RETRY_ATTEMPTS times on failure.
    Pass either `period` (e.g. '3y') or `start` (ISO date string).
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            kwargs: dict = {"auto_adjust": True}
            if period:
                kwargs["period"] = period
            elif start:
                kwargs["start"] = start
                kwargs["end"] = (date.today() + timedelta(days=1)).isoformat()

            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(**kwargs)

            if df is None or df.empty:
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            # Normalize index timezone → tz-naive dates
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df.index = df.index.normalize()  # strip time component

            return df

        except Exception as exc:
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)

    return None


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────


def fetch_initial(exchange_key: str, base_ticker: str) -> None:
    """
    Full historical fetch for a ticker that has no local data yet.
    Uses INITIAL_PERIOD from config (e.g. '3y').
    """
    symbol = _yf_symbol(exchange_key, base_ticker)
    df = _fetch_single(symbol, period=INITIAL_PERIOD)
    save(exchange_key, base_ticker, df)


def fetch_incremental(exchange_key: str, base_ticker: str) -> None:
    """
    Incremental fetch: only downloads data newer than the last stored date.
    If no data exists locally, falls back to a full initial fetch.
    """
    last_date = get_last_date(exchange_key, base_ticker)
    if last_date is None:
        fetch_initial(exchange_key, base_ticker)
        return

    # Start from the day AFTER the last stored candle
    start_str = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = date.today().isoformat()

    if start_str > today_str:
        return

    symbol = _yf_symbol(exchange_key, base_ticker)
    df = _fetch_single(symbol, start=start_str)
    save(exchange_key, base_ticker, df)


def run_full_exchange_fetch(exchange_key: str, incremental: bool = False) -> dict:
    """
    Fetch all tickers for one exchange in batches.

    Args:
        exchange_key:  Key from config.EXCHANGES (e.g. 'PSX', 'US', 'SAUDI')
        incremental:   True → only fetch new data; False → full historical fetch

    Returns:
        Summary dict with counts of success / skipped / failed tickers.
    """
    tickers = EXCHANGES[exchange_key]["tickers"]
    total = len(tickers)
    results = {"exchange": exchange_key, "total": total, "success": 0, "failed": 0}

    mode = "incremental" if incremental else "initial"

    for batch_start in range(0, total, BATCH_SIZE):

        if _shutdown_event.is_set():
            logger.info(
                "Shutdown requested — stopping fetch early at batch %d", batch_start
            )
            break

        batch = tickers[batch_start : batch_start + BATCH_SIZE]

        for base_ticker in batch:
            try:
                if incremental:
                    fetch_incremental(exchange_key, base_ticker)
                else:
                    fetch_initial(exchange_key, base_ticker)
                results["success"] += 1
            except Exception as exc:
                results["failed"] += 1

        # Pause between batches to be polite to yfinance
        if batch_start + BATCH_SIZE < total:
            # time.sleep(BATCH_DELAY_SECONDS)
            _shutdown_event.wait(timeout=BATCH_DELAY_SECONDS)

    return results


def run_all_exchanges(incremental: bool = False) -> list[dict]:
    """Fetch all configured exchanges sequentially."""
    return [run_full_exchange_fetch(k, incremental=incremental) for k in EXCHANGES]


# ─────────────────────────────────────────────
# Track whether initial fetch is running
# ─────────────────────────────────────────────
_fetch_lock = threading.Lock()
_fetch_status: dict = {"running": False, "last_result": None}


def _is_first_run() -> bool:
    from dependencies.market_data.data_store import list_stored_tickers

    for exchange_key in EXCHANGES:
        if list_stored_tickers(exchange_key):
            return False
    return True


def _background_fetch(incremental: bool, exchange_key: Optional[str] = None) -> None:
    with _fetch_lock:
        _fetch_status["running"] = True
        _fetch_status["last_result"] = None
        try:
            if exchange_key:
                results = [
                    run_full_exchange_fetch(exchange_key, incremental=incremental)
                ]
            else:
                results = run_all_exchanges(incremental=incremental)
            _fetch_status["last_result"] = results
        finally:
            _fetch_status["running"] = False
