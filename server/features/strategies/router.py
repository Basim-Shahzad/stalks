import asyncio
import uuid
from datetime import datetime
from typing import Annotated, Callable

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from api.deps import DBSession
from core.logger import logger
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
from features.base.exceptions import ValidationException
from features.portfolios.holdings import OversellError, TransactionSideError
from features.portfolios.repository import PortfolioRepository
from features.portfolios.service import PortfolioService
from features.transactions.repository import TransactionRepository

from .sell.bracket import BracketStrategy

router = APIRouter(prefix="/strategies", tags=["Strategies"])

# The *_pct parameters are multipliers applied to a price, e.g. 1.05 means
# "+5%" and 0.97 means "-3%".
Multiplier = Annotated[float, Query(gt=0, le=10)]
VolumeFraction = Annotated[float, Query(gt=0, le=1)]


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

    transactions = await TransactionRepository(db).list_for_portfolio(portfolio.id)
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


async def _generate_csv(build_csv: Callable[[], str], label: str) -> str:
    """Run the (blocking: live PSX quotes) CSV generation off the event loop
    and translate failures into meaningful HTTP errors."""
    try:
        return await asyncio.to_thread(build_csv)
    except (OversellError, TransactionSideError) as exc:
        raise ValidationException(f"Cannot generate {label} orders: {exc}") from exc
    except (requests.RequestException, ValueError) as exc:
        logger.exception("Live price lookup failed while generating %s CSV", label)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch live prices from PSX",
        ) from exc
    except Exception as exc:
        logger.exception("Failed to generate %s CSV", label)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate {label} orders CSV",
        ) from exc


def _csv_response(csv_content: str, filename: str) -> Response:
    return Response(
        content=csv_content,
        media_type="text/csv",
        status_code=status.HTTP_200_OK,
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
    )


@router.get("/bracket/csv/limit", response_class=Response)
async def get_limit_csv(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: Multiplier,
    upper_sell_bracket_pct: Multiplier,
    stop_price_pct: Multiplier,
    sell_volume_pct: VolumeFraction,
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

    csv_content = await _generate_csv(strategy.to_limit_csv_basket, "limit")
    return _csv_response(csv_content, f"limit_{datetime.now().date()}")


@router.get("/bracket/csv/slo", response_class=Response)
async def get_slo_csv(
    portfolio_id: uuid.UUID,
    account_id: int,
    trigger_pct: Multiplier,
    upper_sell_bracket_pct: Multiplier,
    stop_price_pct: Multiplier,
    sell_volume_pct: VolumeFraction,
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

    csv_content = await _generate_csv(strategy.to_slo_csv_basket, "SLO")
    return _csv_response(csv_content, f"slo_{datetime.now().date()}")
