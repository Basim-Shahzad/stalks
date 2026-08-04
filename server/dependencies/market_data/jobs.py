import asyncio
import os
from core.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from db.database import AsyncSessionLocal
from dependencies.market_data import config as market_settings
from dependencies.market_data.get_tickers import get_merged_exchanges
from services.market_data_service import run_all_exchanges, _fetch_lock, _fetch_status

_scheduler = BackgroundScheduler(timezone=market_settings.SCHEDULER_TIMEZONE)


async def _refresh_ticker_config() -> None:
    async with AsyncSessionLocal() as db:
        merged = await get_merged_exchanges(db)
        market_settings.EXCHANGES.update(merged)


def _nightly_job() -> None:
    if not _fetch_lock.acquire(blocking=False):
        logger.warning("Nightly job skipped — fetch already running.")
        return
    try:
        _fetch_status["running"] = True
        # APScheduler runs this in its own thread, so it is safe to spin up
        # a fresh event loop for the async DB work here.
        asyncio.run(_refresh_ticker_config())

        results = run_all_exchanges(incremental=True)
        for r in results:
            logger.info(
                "  %s → success=%d  failed=%d", r["exchange"], r["success"], r["failed"]
            )
    finally:
        _fetch_status["running"] = False
        _fetch_lock.release()


def start() -> None:
    """Start the background scheduler. Call once at app startup."""
    trigger = CronTrigger(
        hour=market_settings.DAILY_JOB_HOUR,
        minute=market_settings.DAILY_JOB_MINUTE,
        timezone=market_settings.SCHEDULER_TIMEZONE,
    )
    _scheduler.add_job(_nightly_job, trigger, id="nightly_fetch", replace_existing=True)
    _scheduler.start()
    logger.info(
        "Scheduler started — nightly job at %02d:%02d %s",
        market_settings.DAILY_JOB_HOUR,
        market_settings.DAILY_JOB_MINUTE,
        market_settings.SCHEDULER_TIMEZONE,
    )


def stop() -> None:
    """Gracefully shut down the scheduler. Called at app teardown."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def get_next_run() -> str | None:
    """Return ISO string of next scheduled run, or None."""
    job = _scheduler.get_job("nightly_fetch")
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None
