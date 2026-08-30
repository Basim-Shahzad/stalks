from fastapi import APIRouter
from features.auth.router import router as auth_router
from features.portfolios.router import router as portfolios_router
from features.transactions.router import router as transactions_router
from features.transactions.router import jobs_router
from api.v1.endpoints import market_data
from api.v1.endpoints import strategies

api_router = APIRouter()

api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(portfolios_router)
api_router.include_router(transactions_router)
api_router.include_router(jobs_router)
api_router.include_router(market_data.router, prefix="/market", tags=["Market Data"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
