from app.services.transactions_scripts.munir_khanani_parser import process_statement
from app.models import Transaction
from app import db
from pathlib import Path
from datetime import date
import logging
import json
import os

TRANSACTIONS_OUTPUT_FILE = os.environ.get(
    "TRANSACTIONS_OUTPUT_FILE", "transactions_v1.json"
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
OUTPUT_PATH = BASE_DIR / "app" / "data" / TRANSACTIONS_OUTPUT_FILE


def process_file(file_path: str | Path) -> dict:
    path = Path(file_path)

    # --- input validation ---
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

    # --- parse (this already writes JSON once) ---
    try:
        transactions = process_statement(
            str(path),
            output_json_path=str(OUTPUT_PATH),  # ✅ single source of JSON writing
        )
    except FileNotFoundError as exc:
        return {"success": False, "error": str(exc)}
    except ValueError as exc:
        logger.error("Parsing failed for %s: %s", file_path, exc)
        return {"success": False, "error": f"Parsing error: {exc}"}
    except RuntimeError as exc:
        logger.error("Sector lookup failed for %s: %s", file_path, exc)
        return {"success": False, "error": f"Sector lookup error: {exc}"}
    except Exception as exc:
        logger.exception("Unexpected error processing %s", file_path)
        return {"success": False, "error": f"Unexpected error: {exc}"}

    # --- persist to database ---
    try:
        db_records = []

        for t in transactions:
            raw_date = t.get("date")

            # ensure DB gets a date object
            if isinstance(raw_date, str):
                raw_date = date.fromisoformat(raw_date)

            record = Transaction(
                transaction_date=raw_date,
                company=t["company"],
                symbol=t["symbol"],
                sector=t.get("sector"),
                buy=t.get("buy", 0.0),
                sell=t.get("sell", 0.0),
                rate=t["rate"],
                commission=t.get("commission", 0.0),
                taxes=t.get("taxes", 0.0),
                charges=t.get("charges", 0.0),
                total_amount=t["total_amount"],
            )

            db_records.append(record)

        db.session.add_all(db_records)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        logger.exception("Failed to persist transactions to database")
        return {"success": False, "error": f"Database error: {exc}"}

    # --- return API-safe response ---
    return {
        "success": True,
        "data": [
            {
                **t,
                "date": (
                    t["date"].isoformat()
                    if isinstance(t.get("date"), date)
                    else t["date"]
                ),
            }
            for t in transactions
        ],
        "count": len(transactions),
    }
