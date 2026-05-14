from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from schemas.TransactionsSchema import (
    TransactionsListItemSchema,
    TransactionCreateSchema,
    TransactionUpdateSchema,
)
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------------------------------------------------------
# Transactions CRUD
# ---------------------------------------------------------------------------


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
    db: Session, transaction_in: TransactionCreateSchema
) -> Transaction:
    """Creates a new transaction in the database."""
    transaction_data = transaction_in.model_dump()
    db_transaction = Transaction(**transaction_data)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction
