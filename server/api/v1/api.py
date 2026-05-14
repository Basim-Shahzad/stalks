from fastapi import APIRouter
from api.v1.endpoints import auth
from api.v1.endpoints import transactions
from api.v1.endpoints import portfolios

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["Transactions"]
)