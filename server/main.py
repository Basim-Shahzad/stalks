import threading
from core.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.base.exception_handlers import register_exception_handlers
from models.events import transaction_events
from features.auth.models.User import User
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from features.auth.models.RefreshToken import RefreshToken
from models.WatchedSymbol import WatchedSymbol
from db.database import Base, engine, AsyncSessionLocal
from api.v1.api import api_router
from core.config import settings
from contextlib import asynccontextmanager
from services.market_data_service import (
    _is_first_run,
    _background_fetch,
    stop_background_fetch,
)
from dependencies.market_data import jobs as sched
from dependencies.market_data.get_tickers import get_merged_exchanges
from dependencies.market_data import config as market_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App starting up…")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    thread = None

    register_exception_handlers(app=app)

    async with AsyncSessionLocal() as db:
        merged = await get_merged_exchanges(db)
        market_settings.EXCHANGES.update(merged)
        logger.info(
            "Loaded tickers: %s", {k: len(v["tickers"]) for k, v in merged.items()}
        )

    if _is_first_run():
        thread = threading.Thread(
            target=_background_fetch, kwargs={"incremental": False}, daemon=False
        )
        thread.start()

    sched.start()

    yield  # ----------------- APP IS RUNNING HERE -----------------

    logger.info("Shutdown started — stopping background fetch...")
    stop_background_fetch()
    if thread is not None:
        thread.join(timeout=300)
    sched.stop()
    logger.info("Shutdown complete.")


app = FastAPI(title="STALKS_BACKEND", lifespan=lifespan)

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
