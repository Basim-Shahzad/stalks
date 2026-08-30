from pathlib import Path

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
