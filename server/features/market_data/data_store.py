import io
from core.logger import logger
from supabase import create_client
from core.config import settings
import pandas as pd
from .config import EXCHANGES

OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]
BUCKET = "market-data"

# Log at module load time so you know client was created
_supabase = create_client(
    settings.supabase_url, settings.supabase_key.get_secret_value()
)
logger.info("Supabase client initialized — bucket: %s", BUCKET)


def save(exchange_key: str, ticker_symbol: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        logger.warning(
            "save() called with empty df for %s/%s — skipping",
            exchange_key,
            ticker_symbol,
        )
        return

    cols_present = [c for c in OHLCV_COLS if c in df.columns]
    df = df[cols_present].copy()

    existing = load_existing(exchange_key, ticker_symbol)
    if existing is not None:
        combined = pd.concat([existing, df])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined.sort_index(inplace=True)
    else:
        combined = df.sort_index()

    path = f"{EXCHANGES[exchange_key]['folder']}/{ticker_symbol}.csv"
    csv_bytes = combined.to_csv(index=True, index_label="Date").encode()

    try:
        _supabase.storage.from_(BUCKET).upload(
            path, csv_bytes, {"content-type": "text/csv", "upsert": "true"}
        )
        logger.debug(
            "Saved %s/%s (%d rows)", exchange_key, ticker_symbol, len(combined)
        )
    except Exception as e:
        logger.error("Failed to save %s/%s: %s", exchange_key, ticker_symbol, e)

APPROX_BYTES_PER_ROW = 60  # tune this to your CSV row width
HEADER_BYTES = 200          # enough to always capture the header line

def load_existing(
    exchange_key: str,
    ticker_symbol: str,
    limit: int | None = None,
) -> pd.DataFrame | None:
    path = f"{EXCHANGES[exchange_key]['folder']}/{ticker_symbol}.csv"
    bucket = _supabase.storage.from_(BUCKET)

    try:
        if limit is None:
            response = bucket.download(path)
        else:
            # Fetch file size from metadata first
            meta = bucket.info(path)  # returns dict with 'size' key
            file_size = meta["size"]

            # How many bytes to grab from the tail
            tail_bytes = limit * APPROX_BYTES_PER_ROW + HEADER_BYTES
            start_byte = max(0, file_size - tail_bytes)

            if start_byte == 0:
                # Small file — just download everything
                response = bucket.download(path)
            else:
                # Grab header + tail slice
                header_chunk = bucket.download(
                    path,
                    options={"headers": {"Range": f"bytes=0-{HEADER_BYTES - 1}"}},
                )
                tail_chunk = bucket.download(
                    path,
                    options={
                        "headers": {"Range": f"bytes={start_byte}-{file_size - 1}"}
                    },
                )
                # Combine: header + tail (tail may have a partial first line — pandas handles it)
                response = header_chunk + tail_chunk

        df = pd.read_csv(io.BytesIO(response), index_col="Date", parse_dates=True)

        if limit:
            df = df.tail(limit)  # trim any overshoot from the partial chunk

        logger.debug("Loaded %s/%s (%d rows)", exchange_key, ticker_symbol, len(df))
        return df

    except Exception:
        return None


def get_last_date(exchange_key: str, ticker_symbol: str) -> pd.Timestamp | None:
    existing = load_existing(exchange_key, ticker_symbol)
    if existing is None or existing.empty:
        return None
    return existing.index.max()


def list_stored_tickers(exchange_key: str) -> list[str]:
    folder = EXCHANGES[exchange_key]["folder"]
    try:
        files = _supabase.storage.from_(BUCKET).list(folder)
        tickers = [f["name"].replace(".csv", "") for f in files]
        logger.debug("list_stored_tickers(%s) → %d tickers", exchange_key, len(tickers))
        return tickers
    except Exception as e:
        logger.error("Failed to list tickers for %s: %s", exchange_key, e)
        return []
