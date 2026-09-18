from fastapi import APIRouter, Depends, HTTPException, status

from core.logger import logger
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
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
    symbol: str,
    limit: int = 365,
    current_user: User = Depends(get_current_active_user),
):
    try:
        data = await get_market_service().get_ohlcv(exchange, symbol, limit)
        return data
    except StalksDataAPIError as exc:
        logger.error(str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch market data from the Stalks Data API",
        ) from exc
