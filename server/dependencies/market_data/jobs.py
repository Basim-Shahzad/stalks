from core.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from db.database import SessionLocal
from dependencies.market_data import config as market_settings
from dependencies.market_data.get_tickers import get_merged_exchanges
from services.market_data_service import run_all_exchanges

_scheduler = BackgroundScheduler(timezone=market_settings.SCHEDULER_TIMEZONE)


def _nightly_job() -> None:
    logger.info(
        "Nightly scheduler triggered — running incremental fetch for all exchanges."
    )

    db = SessionLocal()
    try:
        merged = get_merged_exchanges(db)
        market_settings.EXCHANGES.update(merged)
    finally:
        db.close()

    results = run_all_exchanges(incremental=True)
    for r in results:
        logger.info(
            "  %s → success=%d  failed=%d", r["exchange"], r["success"], r["failed"]
        )


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
