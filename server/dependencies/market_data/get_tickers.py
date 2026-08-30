from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.transactions.models.WatchedSymbol import WatchedSymbol
from models.enums import ExchangeType
from dependencies.market_data.config import EXCHANGES

_EXCHANGE_KEY_MAP: dict[ExchangeType, str] = {
    ExchangeType.PSX: "PSX",
    ExchangeType.US: "US",
    ExchangeType.TADAWUL: "SAUDI",
}


async def get_merged_exchanges(db: AsyncSession) -> dict[str, dict]:
    """
    Returns EXCHANGES with tickers pulled from watched_symbols.
    Config tickers (if any remain) are preserved; DB tickers unioned in.
    """
    result = await db.execute(select(WatchedSymbol.symbol, WatchedSymbol.exchange))
    rows = result.all()

    db_tickers: dict[str, set[str]] = {key: set() for key in EXCHANGES}
    for symbol, exchange_type in rows:
        key = _EXCHANGE_KEY_MAP.get(exchange_type)
        if key:
            db_tickers[key].add(symbol.strip().upper())

    merged = {}
    for exchange_key, cfg in EXCHANGES.items():
        config_set = set(cfg["tickers"])
        db_only = db_tickers[exchange_key] - config_set
        combined = list(cfg["tickers"]) + sorted(db_only)
        merged[exchange_key] = {**cfg, "tickers": combined}

    return merged
