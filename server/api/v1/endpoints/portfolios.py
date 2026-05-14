import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.PortfolioSchema import (
    PortfolioListItemSchema,
    PortfolioSchema,
    PortfolioCreateSchema,
    PortfolioUpdateSchema,
)
from crud.crud_portfolios import get_portfolios, create_portfolio
from models.User import User
from dependencies.auth_deps import get_current_active_user

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
