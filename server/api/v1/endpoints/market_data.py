from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dependencies.market_data import jobs as sched
from typing import Optional
from dependencies.market_data.config import DATA_ROOT, EXCHANGES
from dependencies.market_data.data_store import load_existing
from services.market_data_service import _background_fetch, _fetch_status
from db.database import get_db
from dependencies.market_data.get_tickers import get_merged_exchanges
from dependencies.market_data import config as market_settings
from schemas.MarketDataSchema import (
    DataStatusResponse,
    FetchTriggerResponse,
    ExchangeInfo,
    TickerDataResponse,
)

router = APIRouter()


@router.get(
    "/data/status", response_model=DataStatusResponse, status_code=status.HTTP_200_OK
)
def status_market_data():
    stored = {}
    for key, cfg in EXCHANGES.items():
        folder = DATA_ROOT / cfg["folder"]
        stored[key] = len(list(folder.glob("*.csv"))) if folder.exists() else 0

    return {
        "fetch_running": _fetch_status["running"],
        "last_fetch_result": _fetch_status["last_result"],
        "next_scheduled_run": sched.get_next_run(),
        "stored_csv_counts": stored,
    }


@router.get(
    "/exchanges", response_model=dict[str, ExchangeInfo], status_code=status.HTTP_200_OK
)
def exchanges():
    return {
        key: {
            "folder": cfg["folder"],
            "suffix": cfg["suffix"],
            "ticker_count": len(cfg["tickers"]),
            "tickers": cfg["tickers"],
        }
        for key, cfg in EXCHANGES.items()
    }


@router.post(
    "/fetch/initial",
    response_model=FetchTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
def trigger_initial_fetch(
    background_tasks: BackgroundTasks,
    exchange: Optional[str] = None,
):
    """
    Trigger a full 3-year historical fetch.
    Pass ?exchange=PSX (or US / SAUDI) to limit to one exchange.
    """
    if _fetch_status["running"]:
        raise HTTPException(status_code=409, detail="A fetch is already running.")

    if exchange and exchange.upper() not in EXCHANGES:
        raise HTTPException(status_code=404, detail=f"Unknown exchange: {exchange}")

    background_tasks.add_task(
        _background_fetch,
        incremental=False,
        exchange_key=exchange.upper() if exchange else None,
    )
    return {
        "message": "Initial fetch started in background.",
        "exchange": exchange or "ALL",
    }


@router.post(
    "/fetch/incremental",
    response_model=FetchTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
def trigger_incremental_fetch(
    background_tasks: BackgroundTasks,
    exchange: Optional[str] = None,
):
    """
    Trigger an incremental fetch (only new candles since last stored date).
    Pass ?exchange=PSX (or US / SAUDI) to limit to one exchange.
    """
    if _fetch_status["running"]:
        raise HTTPException(status_code=409, detail="A fetch is already running.")

    if exchange and exchange.upper() not in EXCHANGES:
        raise HTTPException(status_code=404, detail=f"Unknown exchange: {exchange}")

    background_tasks.add_task(
        _background_fetch,
        incremental=True,
        exchange_key=exchange.upper() if exchange else None,
    )
    return {
        "message": "Incremental fetch started in background.",
        "exchange": exchange or "ALL",
    }


@router.get(
    "/data/{exchange}/{ticker}",
    response_model=TickerDataResponse,
    status_code=status.HTTP_200_OK,
)
def get_ticker_data(
    exchange: str,
    ticker: str,
    limit: Optional[int] = None,
):
    """
    Return stored OHLCV data for a ticker as JSON.
    Optional ?limit=N returns only the last N rows.
    """
    exchange = exchange.upper()
    if exchange not in EXCHANGES:
        raise HTTPException(status_code=404, detail=f"Unknown exchange: {exchange}")

    ticker = ticker.upper()
    df = load_existing(exchange, ticker)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404, detail=f"No data found for {exchange}/{ticker}"
        )

    if limit:
        df = df.tail(limit)

    return JSONResponse(
        content={
            "exchange": exchange,
            "ticker": ticker,
            "rows": len(df),
            "data": df.reset_index()
            .rename(columns={"index": "Date"})
            .to_dict(orient="records"),
        }
    )


@router.post(
    "/tickers/reload",
    response_model=dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
def reload_tickers(
    db: Session = Depends(get_db),
):
    """Re-read WatchedSymbol table and update EXCHANGES in memory."""
    merged = get_merged_exchanges(db)
    market_settings.EXCHANGES.update(merged)
    return {k: len(v["tickers"]) for k, v in merged.items()}
