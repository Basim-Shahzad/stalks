import asyncio
import uuid

from fastapi import APIRouter, Depends, status

from api.deps import DBSession
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
from features.base.exceptions import ValidationException
from features.transactions.repository import TransactionRepository
from services.psx_service import psx_service

from .holdings import Holdings, OversellError, TransactionSideError
from .repository import PortfolioRepository
from .schemas.PortfolioSchema import (
    PortfolioCreateSchema,
    PortfolioHoldingsResponse,
    PortfolioListItemSchema,
    PortfolioSchema,
)
from .service import PortfolioService

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


def get_portfolio_service(db: DBSession) -> PortfolioService:
    return PortfolioService(PortfolioRepository(db))


@router.get(
    "/",
    response_model=list[PortfolioListItemSchema],
    status_code=status.HTTP_200_OK,
)
async def get_portfolio_list(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    return await get_portfolio_service(db).list_for_user(current_user.id)


@router.post(
    "/",
    response_model=PortfolioSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_portfolio_endpoint(
    portfolio_in: PortfolioCreateSchema,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    return await get_portfolio_service(db).create_for_user(portfolio_in, current_user.id)


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioSchema,
    status_code=status.HTTP_200_OK,
)
async def get_portfolio(
    portfolio_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    return await get_portfolio_service(db).get_owned_or_404(portfolio_id, current_user.id)


@router.get(
    "/{portfolio_id}/holdings",
    response_model=PortfolioHoldingsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_portfolio_holdings(
    portfolio_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    portfolio = await get_portfolio_service(db).get_owned_or_404(
        portfolio_id, current_user.id
    )

    transactions = await TransactionRepository(db).list_for_portfolio(portfolio.id)

    # Holdings math is CPU-only but the price enrichment is a blocking HTTP
    # call, so keep the whole thing off the event loop.
    try:
        holdings = await asyncio.to_thread(
            Holdings.from_transactions, transactions, psx_service
        )
    except (OversellError, TransactionSideError, ValueError) as exc:
        raise ValidationException(f"Cannot compute holdings: {exc}") from exc
    return holdings.to_dict()
