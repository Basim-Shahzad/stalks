from core.logger import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from functools import lru_cache

import psxdata as psx
import yfinance as yf

from models.Portfolio import Portfolio
from models.Transaction import Transaction
from models.enums import ExchangeType

# ---------------------------------------------------------------------------
# Price fetching — BATCH first, per-symbol fallback
# ---------------------------------------------------------------------------


def _batch_fetch_yfinance(symbols: list[str]) -> dict[str, float]:
    """
    Fetch all yFinance symbols in a SINGLE HTTP call via yf.download().
    Falls back to per-symbol Ticker() only for any that come back empty.
    """
    if not symbols:
        return {}

    prices: dict[str, float] = {}

    try:
        # group_by="ticker" keeps columns as a MultiIndex (ticker, OHLCV)
        df = yf.download(
            symbols,
            period="2d",  # 2d buffer handles weekends / holidays
            auto_adjust=True,
            progress=False,
            threads=True,  # yfinance internal threading
            group_by="ticker",
        )

        if not df.empty:
            if len(symbols) == 1:
                # Single-ticker download returns flat columns
                sym = symbols[0]
                if "Close" in df.columns and not df["Close"].dropna().empty:
                    prices[sym] = float(df["Close"].dropna().iloc[-1])
            else:
                for sym in symbols:
                    try:
                        close = df[sym]["Close"].dropna()
                        if not close.empty:
                            prices[sym] = float(close.iloc[-1])
                    except (KeyError, IndexError):
                        pass  # will be caught by fallback below
    except Exception:
        logger.exception("yf.download batch failed — falling back to per-symbol")

    # Per-symbol fallback only for anything that didn't resolve
    missing = [s for s in symbols if s not in prices]
    if missing:
        logger.debug(
            "yFinance: per-symbol fallback for %d symbols: %s", len(missing), missing
        )
        with ThreadPoolExecutor(max_workers=min(32, len(missing))) as pool:
            future_to_sym = {
                pool.submit(_get_price_yfinance_single, s): s for s in missing
            }
            for fut in as_completed(future_to_sym):
                sym = future_to_sym[fut]
                try:
                    prices[sym] = fut.result()
                except Exception:
                    logger.exception("yFinance per-symbol fallback failed for %s", sym)
                    prices[sym] = 0.0

    return prices


def _batch_fetch_psx(symbols: list[str]) -> dict[str, float]:
    """
    PSX has no official batch endpoint, so we parallelise aggressively
    with a large thread pool (pure I/O wait).
    """
    if not symbols:
        return {}

    prices: dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=min(32, len(symbols))) as pool:
        future_to_sym = {pool.submit(_get_price_psx_single, s): s for s in symbols}
        for fut in as_completed(future_to_sym):
            sym = future_to_sym[fut]
            try:
                prices[sym] = fut.result()
            except Exception:
                logger.exception("PSX fetch failed for %s", sym)
                prices[sym] = 0.0

    return prices


# ---------------------------------------------------------------------------
# Per-symbol fetchers (used as fallbacks / PSX workers)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=512)
def _get_price_psx_single(symbol: str) -> float:
    try:
        q = psx.quote(symbol)
        if q is not None and not q.empty:
            if "ldcp" in q.columns:
                return float(q["ldcp"].iloc[0])
            for col in ("close", "Close", "last", "Last"):
                if col in q.columns:
                    return float(q[col].iloc[0])
    except Exception:
        logger.debug("PSX quote() failed for %s, trying stocks()", symbol)

    try:
        end = date.today()
        start = end - timedelta(days=7)
        df = psx.stocks(symbol, start=start, end=end)
        if df is not None and not df.empty:
            close_col = next((c for c in df.columns if c.lower() == "close"), None)
            if close_col:
                return float(df[close_col].iloc[-1])
    except Exception:
        logger.exception("PSX stocks() failed for %s", symbol)

    logger.warning("PSX: could not retrieve price for %s — returning 0.0", symbol)
    return 0.0


@lru_cache(maxsize=512)
def _get_price_yfinance_single(symbol: str) -> float:
    try:
        hist = yf.Ticker(symbol).history(period="2d")
        if not hist.empty:
            return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        logger.exception("yFinance per-symbol fetch failed for %s", symbol)

    logger.warning("yFinance: could not retrieve price for %s — returning 0.0", symbol)
    return 0.0


# ---------------------------------------------------------------------------
# Public price entry point
# ---------------------------------------------------------------------------


def _fetch_prices_concurrently(
    symbols: list[str],
    exchange: ExchangeType,
) -> dict[str, float]:
    """
    Fetch prices for all symbols as efficiently as possible.
    - yFinance: one batch download call (drastically faster for many symbols)
    - PSX:      parallel per-symbol calls (no batch API available)
    """
    if not symbols:
        return {}

    if exchange == ExchangeType.PSX:
        return _batch_fetch_psx(symbols)
    return _batch_fetch_yfinance(symbols)


def get_current_price(symbol: str, exchange: ExchangeType) -> float:
    """Single-symbol convenience wrapper (used outside stats if needed)."""
    if exchange == ExchangeType.PSX:
        return _get_price_psx_single(symbol)
    return _get_price_yfinance_single(symbol)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _f(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _get_side(t: Transaction) -> str:
    return t.side.value if hasattr(t.side, "value") else str(t.side)


def _build_holdings(transactions: list[Transaction]) -> dict[str, float]:
    holdings: dict[str, float] = {}
    for t in transactions:
        qty = _f(t.quantity)
        side = _get_side(t)
        if side == "BUY":
            holdings[t.symbol] = holdings.get(t.symbol, 0.0) + qty
        elif side == "SELL":
            holdings[t.symbol] = holdings.get(t.symbol, 0.0) - qty
    return {sym: qty for sym, qty in holdings.items() if qty > 0}


def _avg_buy_price(buys: list[Transaction]) -> float:
    total_qty = sum(_f(t.quantity) for t in buys)
    if total_qty == 0:
        return 0.0
    return sum(_f(t.quantity) * _f(t.rate) for t in buys) / total_qty


# ---------------------------------------------------------------------------
# Stat computations
# ---------------------------------------------------------------------------


def compute_total_invested(transactions: list[Transaction]) -> float:
    return sum(_f(t.total_amount) for t in transactions if _get_side(t) == "BUY")


def compute_total_costs(transactions: list[Transaction]) -> float:
    return sum(_f(t.commission) + _f(t.taxes) + _f(t.charges) for t in transactions)


def compute_realized_profit(transactions: list[Transaction]) -> float:
    grouped: dict[str, list[Transaction]] = {}
    for tx in transactions:
        grouped.setdefault(tx.symbol, []).append(tx)

    total = 0.0
    for txs in grouped.values():
        buys = [t for t in txs if _get_side(t) == "BUY"]
        sells = [t for t in txs if _get_side(t) == "SELL"]
        if not buys or not sells:
            continue

        running_qty = 0.0
        running_cost_basis = 0.0

        for t in sorted(
            txs, key=lambda x: getattr(x, "date", 0) if getattr(x, "date", None) else 0
        ):
            side = _get_side(t)
            if side == "BUY":
                qty = _f(t.quantity)
                if qty > 0:
                    running_cost_basis = (
                        (running_cost_basis * running_qty) + (_f(t.rate) * qty)
                    ) / (running_qty + qty)
                    running_qty += qty
            elif side == "SELL":
                qty = _f(t.quantity)
                if qty <= 0 or running_qty <= 0:
                    continue
                qty = min(qty, running_qty)
                sell_costs = _f(t.commission) + _f(t.taxes) + _f(t.charges)
                total += (_f(t.rate) - running_cost_basis) * qty - sell_costs
                running_qty -= qty

    return total


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def get_portfolio_stats(
    transactions: list[Transaction],
    portfolio: Portfolio,
) -> dict:
    exchange = portfolio.exchange

    # ── Fetch ALL prices in one batch call ───────────────────────────────
    holdings = _build_holdings(transactions)
    prices = _fetch_prices_concurrently(list(holdings.keys()), exchange)

    # ── Group transactions per symbol for cost-basis calc ─────────────────
    grouped: dict[str, list[Transaction]] = {}
    for tx in transactions:
        grouped.setdefault(tx.symbol, []).append(tx)

    # ── Build per-holding detail ──────────────────────────────────────────
    holdings_detail = []
    unrealized_profit = 0.0
    portfolio_value = 0.0

    for symbol, qty in holdings.items():
        txs = grouped.get(symbol, [])
        running_qty = 0.0
        avg_cost = 0.0

        for t in sorted(
            txs, key=lambda x: getattr(x, "date", 0) if getattr(x, "date", None) else 0
        ):
            side = _get_side(t)
            if side == "BUY":
                t_qty = _f(t.quantity)
                if t_qty > 0:
                    avg_cost = ((avg_cost * running_qty) + (_f(t.rate) * t_qty)) / (
                        running_qty + t_qty
                    )
                    running_qty += t_qty
            elif side == "SELL":
                running_qty -= _f(t.quantity)

        current_price = prices.get(symbol, 0.0)
        market_value = qty * current_price
        unrealized = (current_price - avg_cost) * qty
        unrealized_pct = ((current_price / avg_cost) - 1) * 100 if avg_cost else 0.0

        portfolio_value += market_value
        unrealized_profit += unrealized

        holdings_detail.append(
            {
                "symbol": symbol,
                "quantity": qty,
                "avg_buy_price": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_profit": unrealized,
                "unrealized_pct": unrealized_pct,
            }
        )

    holdings_detail.sort(key=lambda x: x["market_value"], reverse=True)

    # ── Aggregate stats ───────────────────────────────────────────────────
    total_invested = compute_total_invested(transactions)
    total_costs = compute_total_costs(transactions)
    realized_profit = compute_realized_profit(transactions)
    total_profit = realized_profit + unrealized_profit
    total_return_pct = (total_profit / total_invested * 100) if total_invested else 0.0

    return {
        "total_invested": total_invested,
        "portfolio_value": portfolio_value,
        "total_costs": total_costs,
        "realized_profit": realized_profit,
        "unrealized_profit": unrealized_profit,
        "total_profit": total_profit,
        "total_return_pct": total_return_pct,
        "holdings": holdings_detail,
    }
