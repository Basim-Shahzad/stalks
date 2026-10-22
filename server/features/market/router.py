from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from core.logger import logger
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
from models.enums import ExchangeType
from services.stalks_data_client import StalksDataAPIError, StalksDataClient

from .schemas.MarketSchema import MarketDataResponse
from .service import MarketService

router = APIRouter(prefix="/market", tags=["Market"])


def get_market_service() -> MarketService:
    return MarketService(StalksDataClient())


@router.get(
    "/data/{exchange}/{symbol}",
    response_model=MarketDataResponse,
    status_code=status.HTTP_200_OK,
)
async def get_market_data(
    exchange: str,
    symbol: Annotated[str, Path(pattern=r"^[A-Za-z0-9._-]{1,20}$")],
    limit: Annotated[int, Query(ge=1, le=5000)] = 365,
    current_user: User = Depends(get_current_active_user),
):
    try:
        exchange_type = ExchangeType(exchange.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown exchange {exchange!r}",
        )

    try:
        return await get_market_service().get_ohlcv(exchange_type.value, symbol, limit)
    except StalksDataAPIError as exc:
        logger.error(str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch market data from the Stalks Data API",
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        # Upstream returned rows in an unexpected shape.
        logger.exception("Malformed market data for %s/%s", exchange_type.value, symbol)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed market data from the Stalks Data API",
        ) from exc
