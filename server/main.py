from core.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.base.exception_handlers import register_exception_handlers
from features.auth.models.User import User
from features.portfolios.models.Portfolio import Portfolio
from features.transactions.models.Transaction import Transaction
from features.auth.models.RefreshToken import RefreshToken
from features.auth.repository import TokenRepository
from db.database import Base, engine, AsyncSessionLocal
from api.v1.api import api_router
from core.config import settings
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy import update

from models.Job import Job, JobStatus
from services.stalks_data_client import StalksDataClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App starting up…")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Background jobs run in-process, so any job still PENDING/IN_PROGRESS at
    # startup was killed by the previous shutdown and would otherwise be
    # reported as running forever.
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(Job)
            .where(Job.status.in_([JobStatus.PENDING, JobStatus.IN_PROGRESS]))
            .values(
                status=JobStatus.FAILED,
                error_message="Interrupted by a server restart. Please upload again.",
                completed_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
        if result.rowcount:
            logger.warning("Marked %d interrupted job(s) as FAILED", result.rowcount)

    async with AsyncSessionLocal() as session:
        purged = await TokenRepository(session).purge_stale()
        await session.commit()
        if purged:
            logger.info("Purged %d stale refresh token(s)", purged)

    yield  # ----------------- APP IS RUNNING HERE -----------------

    await StalksDataClient.close_shared_client()
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
