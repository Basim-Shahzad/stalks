from core.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.base.exception_handlers import register_exception_handlers
from features.transactions import events as transaction_events
from features.auth.models.User import User
from features.portfolios.models.Portfolio import Portfolio
from features.transactions.models.Transaction import Transaction
from features.auth.models.RefreshToken import RefreshToken
from db.database import Base, engine, AsyncSessionLocal
from api.v1.api import api_router
from core.config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App starting up…")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # ----------------- APP IS RUNNING HERE -----------------

    logger.info("Shutdown complete.")


app = FastAPI(title="STALKS_BACKEND", lifespan=lifespan)

register_exception_handlers(app=app)

app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/status")
async def status():
    return {"status": "ok", "version": "1.0.0", "environment": settings.app_env}
