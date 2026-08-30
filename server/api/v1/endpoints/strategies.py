import io
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from api.deps import DBSession
from features.auth.models.User import User
from features.portfolios.repository import PortfolioRepository
from features.portfolios.service import PortfolioService
from dependencies.strategies.sell.bracket import BracketStrategy
from features.transactions.repository import TransactionRepository
from dependencies.auth_deps import get_current_active_user

router = APIRouter()


async def _build_strategy(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: float,
    upper_sell_bracket_pct: float,
    stop_price_pct: float,
    sell_volume_pct: float,
    db: DBSession,
    current_user,
) -> BracketStrategy:
    portfolio = await PortfolioService(PortfolioRepository(db)).get_owned_or_404(
        portfolio_id, current_user.id
    )

    transactions = await TransactionRepository(db).list_for_user(
        current_user.id, portfolio_ids=[portfolio_id]
    )
    symbols = list({t.symbol for t in transactions})

    return BracketStrategy(
        symbols=symbols,
        transactions=transactions,
        trigger_pct=trigger_pct,
        account_id=account_id,
        upper_sell_bracket_pct=upper_sell_bracket_pct,
        stop_price_pct=stop_price_pct,
        sell_volume_pct=sell_volume_pct,
    )


def _csv_response(csv_content: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        status_code=status.HTTP_200_OK,
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
    )


@router.get("/bracket/csv/limit", response_class=StreamingResponse)
async def get_limit_csv(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: float,
    upper_sell_bracket_pct: float,
    stop_price_pct: float,
    sell_volume_pct: float,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    strategy = await _build_strategy(
        portfolio_id,
        account_id,
        trigger_pct,
        upper_sell_bracket_pct,
        stop_price_pct,
        sell_volume_pct,
        db,
        current_user,
    )

    try:
        csv_content = strategy.to_limit_csv_basket()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate limit orders CSV",
        )

    return _csv_response(csv_content, f"limit_{datetime.now().date()}")


@router.get("/bracket/csv/slo", response_class=StreamingResponse)
async def get_slo_csv(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: float,
    upper_sell_bracket_pct: float,
    stop_price_pct: float,
    sell_volume_pct: float,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    strategy = await _build_strategy(
        portfolio_id,
        account_id,
        trigger_pct,
        upper_sell_bracket_pct,
        stop_price_pct,
        sell_volume_pct,
        db,
        current_user,
    )

    try:
        csv_content = strategy.to_slo_csv_basket()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate SLO orders CSV",
        )

    return _csv_response(csv_content, f"slo_{datetime.now().date()}")
