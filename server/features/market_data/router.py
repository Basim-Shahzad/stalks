from fastapi import APIRouter, HTTPException, status
from typing import Optional

from api.deps import DBSession

from .config import EXCHANGES
from .data_store import load_existing, list_stored_tickers
from .get_tickers import get_merged_exchanges
from . import config as market_settings
from .schemas.MarketDataSchema import (
    DataStatusResponse,
    ExchangeInfo,
    TickerDataResponse,
)

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get(
    "/data/status", response_model=DataStatusResponse, status_code=status.HTTP_200_OK
)
def status_market_data():
    stored = {key: len(list_stored_tickers(key)) for key in EXCHANGES}

    return {
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
    exchange = exchange.upper()
    if exchange not in EXCHANGES:
        raise HTTPException(status_code=404, detail=f"Unknown exchange: {exchange}")

    ticker = ticker.upper()
    df = load_existing(exchange, ticker, limit)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404, detail=f"No data found for {exchange}/{ticker}"
        )

    if limit:
        df = df.tail(limit)

    records = (
        df.reset_index()
        .rename(columns=str.lower)
        .to_dict(orient="records")
    )

    return {
        "exchange": exchange,
        "ticker": ticker,
        "rows": len(df),
        "data": records,
    }


@router.post(
    "/tickers/reload",
    response_model=dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
async def reload_tickers(db: DBSession):
    merged = await get_merged_exchanges(db)
    market_settings.EXCHANGES.update(merged)
    return {k: len(v["tickers"]) for k, v in merged.items()}
