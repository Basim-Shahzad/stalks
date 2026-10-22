"""
mmk.py
======
PSX Transaction Statement Parser Service
Broker: Munir Khanani Securities (TREC No. 084)

Parses Munir Khanani broker PDF statements and returns structured
transaction data as a list of dicts suitable for JSON serialisation.

Public API
----------
    from features.transactions.parsers.mmk import process_statement

    transactions = await process_statement("statement.pdf")
    # → list[dict] ready for json.dumps / frontend delivery

Each dict contains:
    date, company, symbol, side, quantity, rate,
    commission, taxes, charges, total_amount, sector
"""

from __future__ import annotations
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import asyncio
from core.logger import logger
import re
from pathlib import Path
from typing import Optional

import pdfplumber

from ..sectors import enrich_with_sectors

_TWO_PLACES = Decimal("0.01")
_VALIDATION_TOLERANCE = Decimal("0.05")

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Statement date in header.
# pdfplumber merges multiple header columns onto one line, so the line may look like:
#   "Date :14-04-2026 Transaction Statement To :14-04-2026"
# We use search() (not match()) and allow optional spaces around the colon.
_RE_STMT_DATE = re.compile(r"Date\s*:(\d{2}-\d{2}-\d{4})")

# Company header line (full name only, no ticker):
# e.g. "ADAMJEE INSURANCE COMPANY LTD."
# We detect these because they appear immediately before a ticker-only line.
# A company header is a non-empty line that is NOT a ticker, NOT a tx row,
# NOT boilerplate — we accept it if the NEXT non-empty line is a pure ticker.
_RE_TICKER_ONLY = re.compile(r"^([A-Z][A-Z0-9]{1,9})\s*$")

# Transaction data row (new format):
# Settlement Type  Qty   Rate      Comm.     SST      CDC    CVT/WHT  Others   LAGA     SECP     NCS      Amount
# T+1REG     B BUY  50  81.00    0.1215     0.91     5.00     0.00     0.00    0.17     0.03     0.13  4,062.31
# T+1REG     D SELL  15 196.33   0.0000     0.00     0.00     0.00     0.00    0.12     0.02     0.09 -2,944.71
#
# Columns after settlement token:
#   [B|D]  [BUY|SELL]  qty  rate  comm  sst  cdc  cvt  others  laga  secp  ncs  amount
_RE_TX = re.compile(
    r"^T\+\d+REG\s+"  # settlement token (ignored)
    r"[BD]\s*"  # B/D marker — space optional (pdfplumber merges "D SELL" → "DSELL")
    r"(BUY|SELL)\s+"  # direction
    r"([\d,]+)\s+"  # quantity
    r"([\d,]+\.\d+)\s+"  # rate
    r"([\d,]+\.\d+)\s+"  # commission rate (per-share)
    r"([\d,]+\.\d+)\s+"  # SST     → taxes
    r"([\d,]+\.\d+)\s+"  # CDC     → charges
    r"([\d,]+\.\d+)\s+"  # CVT/WHT → taxes
    r"([\d,]+\.\d+)\s+"  # Others  → charges
    r"([\d,]+\.\d+)\s+"  # LAGA    → charges
    r"([\d,]+\.\d+)\s+"  # SECP    → charges
    r"([\d,]+\.\d+)\s+"  # NCS     → charges
    r"(-?[\d,]+\.\d+)\s*$"  # amount (signed as a cash flow; we store the magnitude)
)

# "Avg. @" summary line — skip these
_RE_AVG = re.compile(r"^Avg\.\s*@")

# "Net" summary line — kept for back-compat, skip
_RE_NET = re.compile(r"^Net\s+\.")

# Normalise month abbreviations: statement date is DD-MM-YYYY, we output DD-MMM-YY
_MONTH_MAP = {
    "01": "JAN",
    "02": "FEB",
    "03": "MAR",
    "04": "APR",
    "05": "MAY",
    "06": "JUN",
    "07": "JUL",
    "08": "AUG",
    "09": "SEP",
    "10": "OCT",
    "11": "NOV",
    "12": "DEC",
}

# ---------------------------------------------------------------------------
# Helpers — pure computation, no I/O; intentionally synchronous
# ---------------------------------------------------------------------------


def _parse_number(s: str) -> Decimal:
    """Remove comma thousands separator and convert to Decimal (never float)."""
    return Decimal(s.replace(",", ""))


def _reformat_date(raw: str) -> str:
    """
    Convert 'DD-MM-YYYY' (new PDF header) or legacy 'DD-MM-YY' to an
    ISO 8601 string (YYYY-MM-DD).

    e.g. '15-04-2026' → '2026-04-15'
         '26-02-26'   → '2026-02-26'

    Raises ValueError if the format is unrecognised.
    """
    parts = raw.split("-")
    if len(parts) != 3 or len(parts[1]) != 2:
        raise ValueError(f"Unexpected date format: {raw!r}")
    day = int(parts[0])
    month = int(parts[1])
    year_raw = parts[2]
    year = int(year_raw) if len(year_raw) == 4 else 2000 + int(year_raw)
    return date(year, month, day).isoformat()  # → "YYYY-MM-DD"


def _is_page_header_line(line: str) -> bool:
    """Skip boilerplate lines that repeat on every page."""
    boilerplate = (
        "Office :",
        "TREC NO.",
        "Web :",
        "Email :",
        "Phones :",
        "FED Reg :",
        "Page :",
        "Date :",
        "Time :",
        "Transaction Statement",
        "With Tax & Commission",
        "Date Item Settlement",
        "PSX BLDG KARACHI",
        "From :",
        "To :",
        "CDC ID :",
        "Client Total :",
        "User :",
        "110310",  # account header
    )
    stripped = line.strip()
    return any(stripped.startswith(b) for b in boilerplate)


# ---------------------------------------------------------------------------
# Validation — pure computation, no I/O; intentionally synchronous
# ---------------------------------------------------------------------------


def validate_transaction(tx: dict) -> None:
    """
    Financial sanity check.
    For BUY rows:  quantity * rate should be close to total_amount (before fees)
    For SELL rows: quantity * rate should be close to abs(total_amount)

    Tolerance: 5 % of gross value to accommodate all fees/taxes.

    Raises
    ------
    ValueError
        If the discrepancy exceeds the tolerance.
    """
    qty = tx["quantity"]
    gross = qty * tx["rate"]
    amt = abs(tx["total_amount"])

    if gross == 0:
        raise ValueError(
            f"[{tx['symbol']} {tx['date']}] qty*rate is zero — cannot validate."
        )

    discrepancy = abs(gross - amt) / gross
    if discrepancy > _VALIDATION_TOLERANCE:
        raise ValueError(
            f"[{tx['symbol']} {tx['date']}] Validation failed: "
            f"qty={qty} × rate={tx['rate']} = {gross:.2f}, "
            f"but total_amount={tx['total_amount']:.2f} "
            f"(discrepancy={discrepancy:.1%} > 5%)."
        )


# ---------------------------------------------------------------------------
# PDF parser
# ---------------------------------------------------------------------------


def _extract_transactions_sync(pdf_path: str) -> list[dict]:
    """Synchronous core of PDF parsing — runs inside a thread-pool worker.

    Do not call this directly from async code; use ``extract_transactions``
    which dispatches it via ``asyncio.to_thread``.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    transactions: list[dict] = []
    current_company: Optional[str] = None
    current_symbol: Optional[str] = None
    statement_date: Optional[str] = None  # ISO 8601 string, set once from header
    pending_company: Optional[str] = None  # company name seen, waiting for ticker

    with pdfplumber.open(str(path)) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            raw_text = page.extract_text()
            if not raw_text:
                logger.warning("Page %d yielded no text — skipping.", page_idx + 1)
                continue

            for line in raw_text.splitlines():
                line = line.strip()
                if not line:
                    continue

                # ----------------------------------------------------------
                # 1. Capture statement date from page header
                # ----------------------------------------------------------
                m_date = _RE_STMT_DATE.search(line)
                if m_date and statement_date is None:
                    statement_date = _reformat_date(m_date.group(1))
                    logger.debug("Statement date: %s", statement_date)
                    continue

                # ----------------------------------------------------------
                # 2. Skip boilerplate lines
                # ----------------------------------------------------------
                if _is_page_header_line(line):
                    continue

                # Skip Net / Avg / Client Total summary rows
                if _RE_NET.match(line) or _RE_AVG.match(line):
                    continue
                if line.startswith("Client Total"):
                    continue
                # Skip the column-header row
                if line.startswith("Settlement") and "Type" in line:
                    continue

                # ----------------------------------------------------------
                # 3. Try to match a transaction row (most common hot path)
                # ----------------------------------------------------------
                m_tx = _RE_TX.match(line)
                if m_tx:
                    if current_symbol is None:
                        raise ValueError(
                            f"Found transaction row before any company header: "
                            f"{line!r}"
                        )
                    if statement_date is None:
                        raise ValueError(
                            "Found transaction row before statement date in header."
                        )

                    (
                        direction,
                        qty_s,
                        rate_s,
                        comm_rate_s,
                        sst_s,
                        cdc_s,
                        cvt_s,
                        others_s,
                        laga_s,
                        secp_s,
                        ncs_s,
                        amount_s,
                    ) = m_tx.groups()

                    qty = _parse_number(qty_s)
                    commission = (qty * _parse_number(comm_rate_s)).quantize(
                        _TWO_PLACES, rounding=ROUND_HALF_UP
                    )
                    taxes = _parse_number(sst_s) + _parse_number(cvt_s)
                    charges = (
                        _parse_number(cdc_s)
                        + _parse_number(others_s)
                        + _parse_number(laga_s)
                        + _parse_number(secp_s)
                        + _parse_number(ncs_s)
                    )

                    transactions.append(
                        {
                            "date": statement_date,
                            "company": current_company,
                            "symbol": current_symbol,
                            "side": direction,  # "BUY" or "SELL"
                            "quantity": qty,
                            "rate": _parse_number(rate_s),
                            "commission": commission,
                            "taxes": taxes,
                            "charges": charges,
                            # The statement signs the amount as a cash flow
                            # (SELL is negative); store the magnitude so BUY and
                            # SELL are both positive, matching the AKD parser.
                            "total_amount": abs(_parse_number(amount_s)),
                        }
                    )
                    continue

                # ----------------------------------------------------------
                # 4. Detect company name / ticker header
                #
                #    The PDF can produce two layouts depending on extraction:
                #
                #    Layout A (two lines):
                #      Line 1: "ADAMJEE INSURANCE COMPANY LTD."
                #      Line 2: "AICL"
                #
                #    Layout B (one line):
                #      "ADAMJEE INSURANCE COMPANY LTD. AICL"
                #
                #    Strategy:
                #      1. Try Layout B first: line ends with an all-caps ticker
                #         preceded by a space — extract both company and ticker.
                #      2. Try Layout A ticker: line is a pure ticker AND we have
                #         a pending_company → commit.
                #      3. Otherwise store as pending_company for Layout A.
                # ----------------------------------------------------------

                # Layout B: "COMPANY NAME TICKER" on one line
                m_inline = re.match(r"^(.+?)\s+([A-Z][A-Z0-9]{1,9})\s*$", line)
                if m_inline:
                    candidate_company = m_inline.group(1).strip()
                    candidate_ticker = m_inline.group(2).strip()
                    is_data = bool(re.match(r"^\d", candidate_company))
                    is_summ = "Total" in candidate_company or "Net" in candidate_company
                    is_tx = candidate_company.startswith("T+")
                    # Only accept if company part looks like a real name
                    # (has at least one space or ends with LTD/LIMITED/etc.)
                    looks_like_name = (
                        " " in candidate_company
                        or candidate_company.endswith(".")
                        or len(candidate_company) > 10
                    )
                    if not is_data and not is_summ and not is_tx and looks_like_name:
                        current_company = candidate_company
                        current_symbol = candidate_ticker
                        pending_company = None
                        logger.debug(
                            "  Section (inline): %s  [%s]",
                            current_company,
                            current_symbol,
                        )
                        continue

                # Layout A — ticker-only line after a pending company name
                m_ticker = _RE_TICKER_ONLY.match(line)
                if m_ticker and pending_company is not None:
                    current_company = pending_company
                    current_symbol = m_ticker.group(1)
                    pending_company = None
                    logger.debug(
                        "  Section (two-line): %s  [%s]",
                        current_company,
                        current_symbol,
                    )
                    continue

                # Store pending company name (Layout A, first line)
                is_data_row = bool(re.match(r"^\d", line))
                is_summary = "Total" in line or "Net" in line or "User :" in line
                is_tx_like = line.startswith("T+")
                if not is_data_row and not is_summary and not is_tx_like:
                    pending_company = line
                    logger.debug("  Pending company: %r", pending_company)
                    continue

                # Anything else: ignore
                logger.debug("  (ignored) %r", line)

    if not transactions:
        raise ValueError("No transactions found in the PDF. Check the format.")

    logger.info("Extracted %d transaction rows.", len(transactions))
    return transactions


async def extract_transactions(pdf_path: str) -> list[dict]:
    """
    Parse a Munir Khanani broker statement PDF (new column-based format) and
    return a list of transaction dicts.

    Runs the blocking pdfplumber extraction in a thread-pool worker via
    ``asyncio.to_thread`` so the FastAPI event loop stays responsive.

    Parameters
    ----------
    pdf_path : str
        Absolute or relative path to the PDF file.

    Returns
    -------
    list[dict]
        Each dict has keys: date, company, symbol, side, quantity, rate,
        commission, taxes, charges, total_amount
        ('sector' is added later by process_statement)

    Raises
    ------
    FileNotFoundError
        If the PDF does not exist.
    ValueError
        If no transactions are found or a row cannot be reliably parsed.
    """
    return await asyncio.to_thread(_extract_transactions_sync, pdf_path)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def process_statement(pdf_path: str) -> list[dict]:
    """
    Full pipeline: extract → validate → enrich sectors.

    Identical rows are deliberately NOT collapsed here: two genuinely
    identical fills on the same day are legitimate. Re-upload protection is
    handled against the database by the import job.

    This is the **single function to import** when integrating this service
    into a FastAPI route.

    Parameters
    ----------
    pdf_path : str
        Path to the Munir Khanani broker statement PDF.

    Returns
    -------
    list[dict]
        Fully enriched transaction records with all fields populated,
        ready to be serialised and sent to the frontend.

    Raises
    ------
    FileNotFoundError
        PDF path does not exist.
    ValueError
        A transaction row is malformed or fails financial validation.
    SectorNotFoundError / SectorFetchError
        A PSX sector lookup fails (see features.transactions.sectors).
    """
    logger.info("=== PSX Statement Parser: starting ===")
    logger.info("Input: %s", pdf_path)

    # Step 1 – extract raw rows from PDF (runs in thread pool)
    transactions = await extract_transactions(pdf_path)

    # Step 2 – validate each row (pure computation, sync)
    for tx in transactions:
        validate_transaction(tx)

    # Step 3 – fetch & attach PSX sectors (cached, bounded concurrency)
    await enrich_with_sectors(transactions)

    logger.info("=== PSX Statement Parser: done (%d records) ===", len(transactions))
    return transactions
