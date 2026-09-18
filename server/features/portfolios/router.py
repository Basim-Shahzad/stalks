import uuid

from fastapi import APIRouter, Depends, status

from api.deps import DBSession
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
from features.transactions.repository import TransactionRepository
from services.psx_service import PSXScraperService

from .holdings import Holdings
from .repository import PortfolioRepository
from .schemas.PortfolioSchema import (
    PortfolioAnalytics,
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

    transactions = await TransactionRepository(db).list_for_user(
        current_user.id, portfolio_ids=[portfolio.id]
    )
    psx = PSXScraperService()

    holdings = Holdings.from_transactions(transactions, psx)
    return holdings.to_dict()


@router.get(
    "/{portfolio_id}/analytics",
    response_model=PortfolioAnalytics,
    status_code=status.HTTP_200_OK,
)
async def get_portfolio_analytics(
    portfolio_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    service = get_portfolio_service(db)
    portfolio = await service.get_owned_or_404(portfolio_id, current_user.id)

    transactions = await TransactionRepository(db).list_for_user(
        current_user.id, portfolio_ids=[portfolio.id]
    )

    return service.get_analytics(transactions)
