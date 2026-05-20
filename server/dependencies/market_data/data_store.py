"""
data_store.py — Handles all CSV read/write operations.
"""

from pathlib import Path
import pandas as pd
from .config import DATA_ROOT, EXCHANGES

# OHLCV columns we care about (yfinance column names)
OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]


def _exchange_dir(exchange_key: str) -> Path:
    """Return (and create if needed) the folder for a given exchange."""
    folder = EXCHANGES[exchange_key]["folder"]
    path = DATA_ROOT / folder
    path.mkdir(parents=True, exist_ok=True)
    return path


def _csv_path(exchange_key: str, ticker_symbol: str) -> Path:
    """Return the CSV path for a specific ticker."""
    return _exchange_dir(exchange_key) / f"{ticker_symbol}.csv"


def load_existing(exchange_key: str, ticker_symbol: str) -> pd.DataFrame | None:
    """
    Load existing CSV data for a ticker.
    Returns a DataFrame (index = Date) or None if the file doesn't exist.
    """
    path = _csv_path(exchange_key, ticker_symbol)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, index_col="Date", parse_dates=True)
        return df
    except Exception as exc:
        return None


def save(exchange_key: str, ticker_symbol: str, df: pd.DataFrame) -> None:
    """
    Persist a DataFrame to the ticker's CSV file.
    Merges with existing data to avoid duplicates, then saves sorted by date.
    """
    if df is None or df.empty:
        return

    # Keep only OHLCV columns that are present
    cols_present = [c for c in OHLCV_COLS if c in df.columns]
    df = df[cols_present].copy()

    existing = load_existing(exchange_key, ticker_symbol)
    if existing is not None:
        combined = pd.concat([existing, df])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined.sort_index(inplace=True)
    else:
        combined = df.sort_index()

    path = _csv_path(exchange_key, ticker_symbol)
    combined.to_csv(path, index=True, index_label="Date")


def get_last_date(exchange_key: str, ticker_symbol: str) -> pd.Timestamp | None:
    """Return the most recent date stored for a ticker, or None."""
    existing = load_existing(exchange_key, ticker_symbol)
    if existing is None or existing.empty:
        return None
    return existing.index.max()


def list_stored_tickers(exchange_key: str) -> list[str]:
    """List ticker symbols that already have CSV files for an exchange."""
    directory = _exchange_dir(exchange_key)
    return [p.stem for p in directory.glob("*.csv")]
