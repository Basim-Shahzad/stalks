from app.services.transactions_scripts.munir_khanani_parser import process_statement
from pathlib import Path
import logging
import json
import os

TRANSACTIONS_OUTPUT_FILE = os.environ.get('TRANSACTIONS_OUTPUT_FILE', 'transactions_v1.json')

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
OUTPUT_PATH = BASE_DIR / "app" / "data" / TRANSACTIONS_OUTPUT_FILE

def process_file(file_path: str | Path) -> dict:
    """
    Parse a Munir Khanani broker statement PDF and return a structured result.

    Parameters
    ----------
    file_path : str | Path
        Path to the broker statement PDF.

    Returns
    -------
    dict
        On success:  { "success": True,  "data": list[dict], "count": int }
        On failure:  { "success": False, "error": str }
    """
    # --- input validation ---
    path = Path(file_path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    if path.suffix.lower() != ".pdf":
        return {"success": False, "error": f"Expected a PDF file, got: {path.suffix!r}"}

    if path.stat().st_size == 0:
        return {"success": False, "error": "File is empty."}

    # --- ensure output directory exists ---
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {"success": False, "error": f"Cannot create output directory: {exc}"}

    # --- load existing data before parsing (so it isn't lost) ---
    existing_transactions = []
    if OUTPUT_PATH.exists() and OUTPUT_PATH.stat().st_size > 0:
        try:
            existing_transactions = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing_transactions, list):
                existing_transactions = []
        except (json.JSONDecodeError, OSError):
            existing_transactions = []

    # --- parse ---
    try:
        transactions = process_statement(str(path), output_json_path=str(OUTPUT_PATH))
    except FileNotFoundError as exc:
        return {"success": False, "error": str(exc)}
    except ValueError as exc:
        # Parsing or validation error — bad PDF content
        logger.error("Parsing failed for %s: %s", file_path, exc)
        return {"success": False, "error": f"Parsing error: {exc}"}
    except RuntimeError as exc:
        # PSX sector lookup failed after retries
        logger.error("Sector lookup failed for %s: %s", file_path, exc)
        return {"success": False, "error": f"Sector lookup error: {exc}"}
    except Exception as exc:
        # Catch-all — never let an unhandled exception reach the caller
        logger.exception("Unexpected error processing %s", file_path)
        return {"success": False, "error": f"Unexpected error: {exc}"}

    # --- append new transactions to existing ones and rewrite the file ---
    merged = existing_transactions + transactions
    try:
        OUTPUT_PATH.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        logger.error("Failed to write merged transactions to %s: %s", OUTPUT_PATH, exc)
        return {"success": False, "error": f"Failed to save merged data: {exc}"}

    return {
        "success": True,
        "data": transactions,
        "count": len(transactions),
    }
