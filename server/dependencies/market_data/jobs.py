import os
from git import Repo
from core.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from db.database import SessionLocal
from dependencies.market_data import config as market_settings
from dependencies.market_data.get_tickers import get_merged_exchanges
from services.market_data_service import run_all_exchanges, _fetch_lock, _fetch_status

_scheduler = BackgroundScheduler(timezone=market_settings.SCHEDULER_TIMEZONE)


def _initialize_and_sync_repo():
    data_root = market_settings.DATA_ROOT

    if not data_root.exists():
        data_root.parent.mkdir(parents=True, exist_ok=True)
        try:
            repo = Repo.clone_from(market_settings.REPO_URL, str(data_root))
            logger.info("Cloned repo successfully.")
        except Exception as e:
            logger.warning(f"Clone failed (empty repo?), initializing fresh: {e}")
            repo = Repo.init(str(data_root))
            repo.create_remote("origin", market_settings.REPO_URL)
    else:
        # Folder exists — check if it's already a git repo
        git_dir = data_root / ".git"
        if not git_dir.exists():
            # Has CSV files but no git — init and add remote
            logger.info("Folder exists but is not a git repo — initializing...")
            repo = Repo.init(str(data_root))
            repo.create_remote("origin", market_settings.REPO_URL)
        else:
            repo = Repo(str(data_root))
    
    repo.remotes.origin.set_url(market_settings.REPO_URL)

    try:
        repo.remotes.origin.pull()
    except Exception as e:
        logger.warning(f"Pull skipped: {e}")  # this is fine, keep going


def _sync_repo_push():
    from datetime import datetime

    repo = Repo(market_settings.DATA_ROOT)
    repo.remotes.origin.set_url(market_settings.REPO_URL)

    repo.git.add(A=True)

    if repo.is_dirty() or repo.untracked_files:
        commit_msg = f"Nightly sync: {datetime.now().strftime('%Y-%m-%d')}"
        repo.index.commit(commit_msg)
        try:
            repo.git.push()
        except Exception:
            active_branch = repo.active_branch.name
            repo.git.push("-u", "origin", active_branch)
        logger.info("Successfully pushed data to GitHub.")
    else:
        logger.info("No new data to push.")


def _nightly_job() -> None:
    logger.info("Nightly scheduler triggered — syncing repo and running fetch.")

    if not _fetch_lock.acquire(blocking=False):
        logger.warning("Nightly job skipped — initial fetch still in progress.")
        return

    try:
        _fetch_status["running"] = True

        # 1. Pull latest data to avoid merge conflicts
        try:
            _initialize_and_sync_repo()
        except Exception as e:
            logger.error(f"Git setup failed: {e}")
            return

        db = SessionLocal()
        try:
            merged = get_merged_exchanges(db)
            market_settings.EXCHANGES.update(merged)
        finally:
            db.close()

        # 2. Run the existing CSV logic (writes directly into DATA_ROOT)
        results = run_all_exchanges(incremental=True)
        for r in results:
            logger.info(
                "  %s → success=%d  failed=%d", r["exchange"], r["success"], r["failed"]
            )

        # 3. Commit and push the updated CSVs to remote
        try:
            _sync_repo_push()
        except Exception as e:
            logger.error(f"Git push failed: {e}")
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
