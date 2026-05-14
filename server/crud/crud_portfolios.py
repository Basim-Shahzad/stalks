from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from models.Portfolio import Portfolio
from schemas.PortfolioSchema import (
    PortfolioListItemSchema,
    PortfolioCreateSchema,
    PortfolioUpdateSchema,
)
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------


def get_portfolios(db: Session, user_id: UUID) -> list[PortfolioListItemSchema]:
    """
    Fetch all Portfolio for a specific User.

    Args:
        db: The database session.
        user_id: The unique identifier of the user.

    Returns:
        A list of Portfolios of a User.
    """
    try:
        query = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
        )

        result = db.execute(query)
        return result.scalars().all()

    except SQLAlchemyError as e:
        # TODO: raise a more specific exception
        raise


def create_portfolio(
    db: Session, portfolio_in: PortfolioCreateSchema, user_id: UUID
) -> Portfolio:
    """Creates a new portfolio in the database."""
    portfolio_data = portfolio_in.model_dump()
    db_portfolio = Portfolio(**portfolio_data, user_id=user_id)
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def get_portfolio_by_id(db: Session, portfolio_id: UUID) -> Portfolio | None:
    """Fetch a single portfolio by their UUID."""
    try:
        query = select(Portfolio).where(Portfolio.id == portfolio_id)

        result = db.execute(query).scalar_one_or_none()
        return result

    except SQLAlchemyError as e:
        # TODO: raise a more specific exception
        raise
