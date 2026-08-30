from fastapi import APIRouter
from features.auth.router import router as auth_router
from features.portfolios.router import router as portfolios_router
from api.v1.endpoints import transactions
from api.v1.endpoints import market_data
from api.v1.endpoints import strategies
from api.v1.endpoints import jobs

api_router = APIRouter()

api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(portfolios_router)
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["Transactions"]
)
api_router.include_router(market_data.router, prefix="/market", tags=["Market Data"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
