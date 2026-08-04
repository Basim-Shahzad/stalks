import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.PortfolioSchema import (
    PortfolioListItemSchema,
    PortfolioSchema,
    PortfolioCreateSchema,
    PortfolioHoldingsResponse,
)
from crud.crud_portfolios import get_portfolios, create_portfolio, get_portfolio_by_id
from crud.crud_transactions import get_transactions
from services.psx_service import PSXScraperService
from features.auth.models.User import User
from dependencies.auth_deps import get_current_active_user
from dependencies.portfolio.holdings import Holdings

router = APIRouter()


@router.get(
    "/",
    response_model=list[PortfolioListItemSchema],
    status_code=status.HTTP_200_OK,
)
def get_portfolio_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    portfolios = get_portfolios(db, current_user.id)

    # Optional: Handle the 404 case if the portfolio doesn't exist
    if portfolios is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return portfolios


@router.post(
    "/",
    response_model=PortfolioSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_portfolio_endpoint(
    portfolio_in: PortfolioCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_portfolio(db, portfolio_in, current_user.id)


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioSchema,
    status_code=status.HTTP_200_OK,
)
def get_portfolio(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return portfolio


@router.get(
    "/{portfolio_id}/holdings",
    status_code=status.HTTP_200_OK,
    response_model=PortfolioHoldingsResponse,
)
def get_portfolio(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = get_transactions(db, current_user.id, portfolios=[portfolio_id])
    psx = PSXScraperService()

    holdings = Holdings.from_transactions(transactions, psx)

    return holdings.to_dict()
