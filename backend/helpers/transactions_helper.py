from app.services.transactions_service import process_file as process_pdf_file
from app import db
from app.models import Transaction
from datetime import date
import csv
import logging

logger = logging.getLogger(__name__)


def parse_transactions_pdf(file_path: str, portfolio_id: str) -> dict:
    """
    Thin wrapper — all the heavy lifting (parsing, DB writes, response shaping)
    lives in transactions_service.process_file.
    """
    return process_pdf_file(file_path, portfolio_id=portfolio_id)


def parse_transactions_csv(file_path: str, portfolio_id: str) -> dict:
    """
    Parses a CSV of transactions, persists them, and returns an API-safe dict.
    Expected columns (case-insensitive, order doesn't matter):
        date, company, symbol, sector, buy, sell, rate,
        commission, taxes, charges, total_amount
    """
    required_columns = {"date", "company", "symbol", "rate", "total_amount"}

    try:
        with open(file_path, newline="", encoding="utf-8-sig") as f:  # utf-8-sig strips BOM if Excel-exported
            reader = csv.DictReader(f)

            # Normalise header names to lowercase stripped strings
            if reader.fieldnames is None:
                return {"success": False, "error": "CSV file appears to be empty or has no header row."}

            normalised_headers = {h.strip().lower() for h in reader.fieldnames}
            missing = required_columns - normalised_headers
            if missing:
                return {
                    "success": False,
                    "error": f"CSV is missing required column(s): {', '.join(sorted(missing))}",
                }

            rows = list(reader)

        if not rows:
            return {"success": False, "error": "CSV has a header but no data rows."}

    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {file_path}"}
    except Exception as exc:
        logger.exception("Failed to read CSV %s", file_path)
        return {"success": False, "error": f"Could not read CSV: {exc}"}

    # --- parse rows ---
    transactions = []
    errors = []

    for i, row in enumerate(rows, start=2):  # start=2 because row 1 is the header
        # Normalise keys once per row
        clean = {k.strip().lower(): v.strip() for k, v in row.items() if k}

        # --- date ---
        try:
            transaction_date = date.fromisoformat(clean["date"])  # expects YYYY-MM-DD
        except (ValueError, KeyError):
            errors.append(f"Row {i}: invalid or missing date '{clean.get('date')}' (expected YYYY-MM-DD).")
            continue

        # --- numeric helpers ---
        def to_float(key: str, default: float = 0.0) -> float:
            raw = clean.get(key, "").replace(",", "")  # handle comma-formatted numbers
            try:
                return float(raw) if raw else default
            except ValueError:
                errors.append(f"Row {i}: '{key}' value '{raw}' is not a valid number.")
                return default

        rate = to_float("rate")
        total_amount = to_float("total_amount")

        if not clean.get("company"):
            errors.append(f"Row {i}: 'company' is required.")
            continue
        if not clean.get("symbol"):
            errors.append(f"Row {i}: 'symbol' is required.")
            continue

        transactions.append({
            "date": transaction_date,
            "company": clean["company"],
            "symbol": clean["symbol"].upper(),
            "sector": clean.get("sector") or None,
            "buy": to_float("buy"),
            "sell": to_float("sell"),
            "rate": rate,
            "commission": to_float("commission"),
            "taxes": to_float("taxes"),
            "charges": to_float("charges"),
            "total_amount": total_amount,
        })

    # Partial failure: tell the caller which rows broke
    if errors and not transactions:
        return {"success": False, "error": "All rows failed to parse.", "row_errors": errors}

    # --- persist ---
    try:
        db_records = [
            Transaction(
                portfolio_id=portfolio_id,
                transaction_date=t["date"],
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
            for t in transactions
        ]

        db.session.add_all(db_records)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        logger.exception("Failed to persist CSV transactions to database")
        return {"success": False, "error": f"Database error: {exc}"}

    return {
        "success": True,
        "skipped_rows": errors if errors else None,   # partial success surfaced here
        "data": [
            {**t, "date": t["date"].isoformat()}
            for t in transactions
        ],
    }