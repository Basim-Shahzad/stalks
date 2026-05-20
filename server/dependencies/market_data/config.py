from pathlib import Path
import pytz

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = BASE_DIR / "core" / "data"  # All exchange folders live here

# ─────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────
SCHEDULER_TIMEZONE = pytz.timezone("Asia/Riyadh")  # AST (UTC+3)
DAILY_JOB_HOUR = 23  # 11 PM AST — after all three markets have closed
DAILY_JOB_MINUTE = 0

# ─────────────────────────────────────────────
# Fetch settings
# ─────────────────────────────────────────────
INITIAL_PERIOD = "3y"  # Used on first-ever fetch
BATCH_SIZE = 10  # Tickers per batch (avoids hammering yfinance)
BATCH_DELAY_SECONDS = 2.0  # Pause between batches
RETRY_ATTEMPTS = 3  # Per-ticker retry count on failure
RETRY_DELAY_SECONDS = 5.0  # Wait between retries

# ─────────────────────────────────────────────
# Exchange definitions
# Each entry:
#   folder   → subfolder inside DATA_ROOT
#   suffix   → appended to raw ticker symbols (empty string for US)
#   tickers  → list of base ticker symbols (without suffix)
# ─────────────────────────────────────────────
EXCHANGES: dict[str, dict] = {
    "PSX": {
        "folder": "psx",
        "suffix": ".KA",
        "tickers": [],
    },
    "US": {
        "folder": "us",
        "suffix": "",
        "tickers": [],
    },
    "SAUDI": {
        "folder": "saudi",
        "suffix": ".SR",
        "tickers": [],
    },
}