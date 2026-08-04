import io
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db.database import get_db
from features.auth.models.User import User
from dependencies.strategies.sell.bracket import BracketStrategy
from crud.crud_transactions import get_transactions
from crud.crud_portfolios import get_portfolio_by_id
from dependencies.auth_deps import get_current_active_user

router = APIRouter()


def _build_strategy(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: float,
    upper_sell_bracket_pct: float,
    stop_price_pct: float,
    sell_volume_pct: float,
    db: Session,
    current_user,
) -> BracketStrategy:
    portfolio = get_portfolio_by_id(db, portfolio_id)

    if portfolio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    transactions = get_transactions(db, portfolio_id)
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
def get_limit_csv(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: float,
    upper_sell_bracket_pct: float,
    stop_price_pct: float,
    sell_volume_pct: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    strategy = _build_strategy(
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
def get_slo_csv(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: float,
    upper_sell_bracket_pct: float,
    stop_price_pct: float,
    sell_volume_pct: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    strategy = _build_strategy(
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
