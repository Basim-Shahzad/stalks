from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from models.enums import ExchangeType
from models.WatchedSymbol import WatchedSymbol
from schemas.TransactionsSchema import (
    TransactionsListItemSchema,
    TransactionCreateSchema,
    TransactionUpdateSchema,
)
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------------------------------------------------------
# Transactions CRUD
# ---------------------------------------------------------------------------


def _ensure_symbol_watched(db: Session, symbol: str, exchange: ExchangeType) -> None:
    """Add to WatchedSymbol if not already there."""
    exists = db.execute(
        select(WatchedSymbol).where(
            WatchedSymbol.symbol == symbol,
            WatchedSymbol.exchange == exchange,
        )
    ).scalar_one_or_none()

    if not exists:
        db.add(WatchedSymbol(symbol=symbol, exchange=exchange))
        db.commit()


def get_transactions(
    db: Session, portfolio_id: UUID
) -> list[TransactionsListItemSchema]:
    """
    Fetch all transactions for a specific Portfolio.

    Args:
        db: The database session.
        portfolio_id: The unique identifier of the portfolio.

    Returns:
        A list of Transactions of a Portfolio.
    """
    try:
        query = (
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.created_at.desc())
        )

        result = db.execute(query)
        return result.scalars().all()

    except SQLAlchemyError as e:
        # TODO: raise a more specific exception
        raise


def create_transaction(
    db: Session, portfolio: Portfolio, transaction_in: TransactionCreateSchema
) -> Transaction:
    """Creates a new transaction in the database."""
    transaction_data = transaction_in.model_dump()
    transaction_data["portfolio_id"] = portfolio.id

    db_transaction = Transaction(**transaction_data)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    _ensure_symbol_watched(db, transaction_in.symbol, portfolio.exchange)

    return db_transaction