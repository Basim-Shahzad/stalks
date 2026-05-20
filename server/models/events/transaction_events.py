"""
transaction_events.py — SQLAlchemy event hooks that keep watched_symbols
in sync whenever a Transaction is inserted or deleted.

Import this module once at app startup (e.g. in main.py) so the hooks register.
"""

from sqlalchemy import event, select, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from models.Transaction import Transaction
from models.Portfolio import Portfolio
from models.enums import ExchangeType
from models.WatchedSymbol import WatchedSymbol


def _get_exchange_for_transaction(
    session: Session, transaction: Transaction
) -> ExchangeType | None:
    """Resolve the exchange from the transaction's portfolio."""
    # Portfolio may already be in the session identity map — avoid extra query if so
    portfolio = transaction.portfolio or session.get(
        Portfolio, transaction.portfolio_id
    )
    if portfolio is None:
        return None
    return portfolio.exchange


def _upsert_watched_symbol(
    session: Session, symbol: str, exchange: ExchangeType
) -> None:
    """Insert (symbol, exchange) into watched_symbols, ignore if already exists."""
    exists = session.execute(
        select(WatchedSymbol).where(
            WatchedSymbol.symbol == symbol,
            WatchedSymbol.exchange == exchange,
        )
    ).scalar_one_or_none()

    if exists is None:
        session.add(WatchedSymbol(symbol=symbol.strip().upper(), exchange=exchange))


def _remove_if_unreferenced(
    session: Session, symbol: str, exchange: ExchangeType
) -> None:
    """
    Remove (symbol, exchange) from watched_symbols only if no other
    transaction still references that symbol on that exchange.
    """
    still_exists = session.execute(
        select(func.count())
        .select_from(Transaction)
        .join(Portfolio, Transaction.portfolio_id == Portfolio.id)
        .where(
            Transaction.symbol == symbol,
            Portfolio.exchange == exchange,
        )
    ).scalar()

    if still_exists == 0:
        row = session.execute(
            select(WatchedSymbol).where(
                WatchedSymbol.symbol == symbol,
                WatchedSymbol.exchange == exchange,
            )
        ).scalar_one_or_none()
        if row:
            session.delete(row)


# ─────────────────────────────────────────────
# Event hooks
# ─────────────────────────────────────────────


@event.listens_for(Transaction, "after_insert")
def on_transaction_insert(mapper, connection, target: Transaction):
    session = Session.object_session(target)
    if session is None:
        return
    exchange = _get_exchange_for_transaction(session, target)
    if exchange:
        _upsert_watched_symbol(session, target.symbol, exchange)


@event.listens_for(Transaction, "after_delete")
def on_transaction_delete(mapper, connection, target: Transaction):
    session = Session.object_session(target)
    if session is None:
        return
    exchange = _get_exchange_for_transaction(session, target)
    if exchange:
        _remove_if_unreferenced(session, target.symbol, exchange)
