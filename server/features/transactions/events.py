"""
events.py — SQLAlchemy event hooks that keep watched_symbols
in sync whenever a Transaction is inserted or deleted.

Import this module once at app startup (e.g. in main.py) so the hooks register.
"""

from sqlalchemy import event, select, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from features.portfolios.models.Portfolio import Portfolio
from models.enums import ExchangeType
from .models.Transaction import Transaction


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
