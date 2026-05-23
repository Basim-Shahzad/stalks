from fastapi import APIRouter
from api.v1.endpoints import auth
from api.v1.endpoints import transactions
from api.v1.endpoints import portfolios
from api.v1.endpoints import market_data
from api.v1.endpoints import strategies

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["Transactions"]
)
api_router.include_router(market_data.router, prefix="/market", tags=["Market Data"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
