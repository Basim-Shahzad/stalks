import threading
from core.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.User import User
from models.Portfolio import Portfolio
from models.Transaction import Transaction
from models.RefreshToken import RefreshToken
from db.database import Base, engine
from api.v1.api import api_router
from core.config import settings
from contextlib import asynccontextmanager
from services.market_data_service import _is_first_run, _background_fetch
from dependencies.market_data import jobs as sched


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App starting up…")

    if _is_first_run():
        logger.info(
            "First run detected — kicking off full historical fetch in background."
        )
        thread = threading.Thread(
            target=_background_fetch, kwargs={"incremental": False}, daemon=True
        )
        thread.start()
    else:
        logger.info("Existing data found — skipping initial fetch.")

    sched.start()

    yield

    Base.metadata.create_all(bind=engine)

    sched.stop()
    logger.info("App shut down.")


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
