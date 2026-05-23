import threading
from core.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.events import transaction_events
from models.User import User
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from models.RefreshToken import RefreshToken
from models.WatchedSymbol import WatchedSymbol
from db.database import Base, engine, SessionLocal
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

    Base.metadata.create_all(bind=engine)
    thread = None

    db = SessionLocal()
    try:
        merged = get_merged_exchanges(db)
        market_settings.EXCHANGES.update(merged)
        logger.info(
            "Loaded tickers: %s", {k: len(v["tickers"]) for k, v in merged.items()}
        )
    finally:
        db.close()

    try:
        sched._initialize_and_sync_repo()
        logger.info("Git repo initialized.")
    except Exception as e:
        logger.error(f"Git init failed: {e}")    

    if _is_first_run():
        def _fetch_then_push():
            _background_fetch(incremental=False)
            logger.info("Initial fetch complete — pushing to GitHub...")
            try:
                sched._initialize_and_sync_repo()  # ensure git is set up first
                sched._sync_repo_push()
            except Exception as e:
                logger.error(f"Initial git push failed: {e}")

        thread = threading.Thread(target=_fetch_then_push, daemon=False)
        thread.start()

    sched.start()

    yield  # ----------------- APP IS RUNNING HERE -----------------

    logger.info("Shutdown started — stopping background fetch...")
    stop_background_fetch()
    if thread is not None:
        thread.join(timeout=30)
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
