"""
munir_khanani_parser.py
=======================
PSX Transaction Statement Parser Service
Broker: Munir Khanani Securities (TREC No. 084)

Parses Munir Khanani broker PDF statements and returns structured
transaction data as a list of dicts suitable for JSON serialisation.

Public API
----------
    from munir_khanani_parser import process_statement

    transactions = process_statement("statement.pdf")
    # → list[dict] ready for json.dumps / frontend delivery

Each dict contains:
    date, company, symbol, buy, sell, rate,
    commission, taxes, charges, total_amount, sector
"""

from __future__ import annotations
from bs4 import BeautifulSoup
from datetime import date
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional
from app.constants.sectors import PSX_SECTORS

import pdfplumber
import requests
import unicodedata

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("munir_khanani_parser")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s  %(name)s: %(message)s"))
    logger.addHandler(_h)

# ---------------------------------------------------------------------------
# Persistent sector cache
# ---------------------------------------------------------------------------
_CACHE_FILE = (
    Path(__file__).parent.parent.parent / "data" / "cache" / "sector_cache.json"
)
_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
_SECTOR_CACHE: dict[str, str] = {}


def _load_cache() -> None:
    """Load sector cache from disk into memory on startup."""
    global _SECTOR_CACHE
    if _CACHE_FILE.exists():
        try:
            _SECTOR_CACHE = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            logger.info("Sector cache loaded: %d symbols", len(_SECTOR_CACHE))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load sector cache: %s — starting fresh", e)
            _SECTOR_CACHE = {}


def _save_cache() -> None:
    """Persist current in-memory cache to disk."""
    try:
        _CACHE_FILE.write_text(
            json.dumps(_SECTOR_CACHE, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as e:
        logger.warning("Could not save sector cache: %s", e)


# Run once at import time
_load_cache()

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
    r"([\d,]+\.\d+)\s+"  # SST  → taxes
    r"([\d,]+\.\d+)\s+"  # CDC  → charges
    r"[\d,]+\.\d+\s+"  # CVT/WHT (ignored)
    r"[\d,]+\.\d+\s+"  # Others  (ignored)
    r"[\d,]+\.\d+\s+"  # LAGA    (ignored)
    r"[\d,]+\.\d+\s+"  # SECP    (ignored)
    r"[\d,]+\.\d+\s+"  # NCS     (ignored)
    r"(-?[\d,]+\.\d+)\s*$"  # amount
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
# Helpers
# ---------------------------------------------------------------------------


def _parse_number(s: str) -> float:
    """Remove comma thousands separator and convert to float."""
    return float(s.replace(",", ""))


def _reformat_date(raw: str) -> date:
    """
    Convert 'DD-MM-YYYY' (new PDF header) or legacy 'DD-MM-YY' to a
    Python ``datetime.date`` object.

    e.g. '15-04-2026' → date(2026, 4, 15)
         '26-02-26'   → date(2026, 2, 26)

    Raises ValueError if the format is unrecognised.
    """
    parts = raw.split("-")
    if len(parts) != 3 or len(parts[1]) != 2:
        raise ValueError(f"Unexpected date format: {raw!r}")
    day = int(parts[0])
    month = int(parts[1])
    year_raw = parts[2]
    year = int(year_raw) if len(year_raw) == 4 else 2000 + int(year_raw)
    return date(year, month, day)


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
# PSX sector lookup
# ---------------------------------------------------------------------------


def _normalize(s: str) -> str:
    """
    Aggressively normalize a sector string for fuzzy comparison.
    Strips accents, punctuation, extra whitespace; uppercases everything.
    "PAPER, BOARD & PACKAGING" → "PAPERBOARDPACKAGING"
    "INV. BANKS / INV. COS. / SECURITIES COS." → "INVBANKSINVCOSSECURITIESCOS"
    """
    s = unicodedata.normalize("NFKD", s)
    s = s.upper()
    s = re.sub(r"[^A-Z0-9\s]", "", s)  # strip all punctuation
    s = re.sub(r"\s+", "", s)  # strip all whitespace
    return s


# Build once at module level — avoids rebuilding on every call
_SECTOR_NORM_MAP: dict[str, str] = {_normalize(s): s for s in PSX_SECTORS}


def get_psx_sector(symbol: str) -> str:
    if symbol in _SECTOR_CACHE:
        return _SECTOR_CACHE[symbol]

    url = f"https://dps.psx.com.pk/company/{symbol}"
    last_error = None

    for attempt in range(1, 4):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            candidates: list[str] = []
            for tag in soup.find_all(True):
                for child in tag.children:
                    if child.name is None:
                        text = str(child).strip()
                        if text:
                            candidates.append(text)

            # Tier 1: exact case-insensitive match
            for text in candidates:
                for canonical in PSX_SECTORS:
                    if text.upper() == canonical.upper():
                        _SECTOR_CACHE[symbol] = canonical
                        _save_cache()
                        logger.info("Sector %-12s → %s  [exact]", symbol, canonical)
                        return canonical

            # Tier 2: normalized match (punctuation/whitespace insensitive)
            for text in candidates:
                norm = _normalize(text)
                if norm in _SECTOR_NORM_MAP:
                    canonical = _SECTOR_NORM_MAP[norm]
                    _SECTOR_CACHE[symbol] = canonical
                    _save_cache()
                    logger.warning(
                        "Sector %-12s → %s  [normalized, raw=%r]",
                        symbol,
                        canonical,
                        text,
                    )
                    return canonical

            # Tier 3: substring match against full page text
            full_page_norm = _normalize(soup.get_text())
            for norm_canonical, canonical in _SECTOR_NORM_MAP.items():
                if norm_canonical in full_page_norm:
                    _SECTOR_CACHE[symbol] = canonical
                    _save_cache()
                    logger.warning(
                        "Sector %-12s → %s  [substring fallback]", symbol, canonical
                    )
                    return canonical

            logger.error(
                "Sector not found for %s. First 30 candidate strings from page:\n%s",
                symbol,
                "\n".join(f"  {c!r}" for c in candidates[:30]),
            )
            raise RuntimeError(
                f"Sector not found in PSX page for {symbol!r}. URL: {url}"
            )

        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "PSX lookup attempt %d/3 failed for %s: %s", attempt, symbol, exc
            )
            if attempt < 3:
                time.sleep(2 * attempt)

    raise RuntimeError(
        f"Failed to fetch PSX sector for {symbol!r} after 3 attempts. "
        f"Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_transaction(tx: dict) -> None:
    """
    Financial sanity check.
    For BUY rows:  qty * rate should be close to total_amount (before fees)
    For SELL rows: qty * rate should be close to abs(total_amount)

    Tolerance: 5 % of gross value to accommodate all fees/taxes.

    Raises
    ------
    ValueError
        If the discrepancy exceeds the tolerance.
    """
    qty = tx["buy"] if tx["buy"] > 0 else tx["sell"]
    gross = qty * tx["rate"]
    amt = abs(tx["total_amount"])

    if gross == 0:
        raise ValueError(
            f"[{tx['symbol']} {tx['date']}] qty*rate is zero — " "cannot validate."
        )

    discrepancy = abs(gross - amt) / gross
    if discrepancy > 0.05:
        raise ValueError(
            f"[{tx['symbol']} {tx['date']}] Validation failed: "
            f"qty={qty} × rate={tx['rate']} = {gross:.2f}, "
            f"but total_amount={tx['total_amount']:.2f} "
            f"(discrepancy={discrepancy:.1%} > 5%)."
        )


# ---------------------------------------------------------------------------
# PDF parser
# ---------------------------------------------------------------------------


def extract_transactions(pdf_path: str) -> list[dict]:
    """
    Parse a Munir Khanani broker statement PDF (new column-based format) and
    return a list of transaction dicts.

    New PDF layout (per page):
      - Header block contains "Date : DD-MM-YYYY" — used as the trade date for
        every transaction on that statement (no per-row date in the new format).
      - Each stock section starts with the full company name on its own line,
        immediately followed by the ticker symbol on the next non-empty line.
      - Transaction rows match _RE_TX (T+1REG ... BUY/SELL qty rate comm ...).
      - "Avg. @" rows and "Client Total" rows are skipped.

    Columns captured from each transaction row:
        direction   BUY or SELL
        qty         share quantity
        rate        trade price per share
        comm_rate   per-share commission rate  → actual = qty × comm_rate
        sst         SST charge                 → schema: taxes
        cdc         CDC charge                 → schema: charges
        amount      net settlement amount (negative for sells)

    Parameters
    ----------
    pdf_path : str
        Absolute or relative path to the PDF file.

    Returns
    -------
    list[dict]
        Each dict has keys: date, company, symbol, buy, sell, rate,
        commission, taxes, charges, total_amount
        ('sector' is added later by process_statement)

    Raises
    ------
    FileNotFoundError
        If the PDF does not exist.
    ValueError
        If no transactions are found or a row cannot be reliably parsed.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    transactions: list[dict] = []
    current_company: Optional[str] = None
    current_symbol: Optional[str] = None
    statement_date: Optional[str] = None  # reformatted once from header
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
                        amount_s,
                    ) = m_tx.groups()

                    qty = _parse_number(qty_s)
                    is_buy = direction == "BUY"
                    buy_qty = qty if is_buy else 0.0
                    sell_qty = qty if not is_buy else 0.0
                    commission = round(qty * _parse_number(comm_rate_s), 2)

                    transactions.append(
                        {
                            "date": statement_date,
                            "company": current_company,
                            "symbol": current_symbol,
                            "buy": buy_qty,
                            "sell": sell_qty,
                            "rate": _parse_number(rate_s),
                            "commission": commission,
                            "taxes": _parse_number(sst_s),
                            "charges": _parse_number(cdc_s),
                            "total_amount": _parse_number(amount_s),
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


# ---------------------------------------------------------------------------
# Sector enrichment
# ---------------------------------------------------------------------------


def _enrich_with_sectors(transactions: list[dict]) -> list[dict]:
    """
    Add a 'sector' key to every transaction by querying PSX.
    Symbols are deduplicated before querying.

    Mutates and returns the input list.
    """
    symbols = sorted({t["symbol"] for t in transactions})
    logger.info("Fetching sectors for %d unique symbols…", len(symbols))

    sector_map: dict[str, str] = {}
    for symbol in symbols:
        sector_map[symbol] = get_psx_sector(symbol)

    for tx in transactions:
        tx["sector"] = sector_map[tx["symbol"]]

    return transactions


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def _check_duplicates(transactions: list[dict]) -> list[dict]:
    """
    Remove exact duplicate rows caused by double API submissions.

    Two rows are considered duplicates when date + symbol + buy + sell +
    rate + total_amount are all identical.  The first occurrence is kept;
    subsequent identical rows are dropped with a warning.

    Genuinely identical trades executed back-to-back on the exchange are
    astronomically unlikely and are also dropped — if that ever becomes a
    real issue, add a timestamp column to the key.

    Returns the deduplicated list.
    """
    seen: dict[tuple, int] = {}
    kept: list[dict] = []
    for i, tx in enumerate(transactions):
        key = (
            tx["date"],
            tx["symbol"],
            tx["buy"],
            tx["sell"],
            tx["rate"],
            tx["total_amount"],
        )
        if key in seen:
            logger.warning(
                "Duplicate REMOVED: row %d is identical to row %d  "
                "(%s %s qty=%s rate=%s). Keeping first occurrence only.",
                i,
                seen[key],
                tx["date"],
                tx["symbol"],
                tx["buy"] or tx["sell"],
                tx["rate"],
            )
        else:
            seen[key] = i
            kept.append(tx)

    removed = len(transactions) - len(kept)
    if removed:
        logger.info("Deduplication: removed %d duplicate row(s).", removed)
    return kept


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------


def save_json(data: list[dict], output_path: str) -> None:
    """
    Write *data* as pretty-printed JSON to *output_path*.
    ``datetime.date`` values are serialised as ISO-8601 strings ("YYYY-MM-DD").

    Parameters
    ----------
    data : list[dict]
        Transaction records as returned by process_statement().
    output_path : str
        Destination file path (will be created or overwritten).
    """

    class _DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, date):
                return obj.isoformat()  # "YYYY-MM-DD"
            return super().default(obj)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, cls=_DateEncoder)
    logger.info("JSON saved → %s  (%d records)", out, len(data))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def process_statement(
    pdf_path: str,
    output_json_path: Optional[str] = None,
) -> list[dict]:
    """
    Full pipeline: extract → validate → enrich sectors → (optionally) save.

    This is the **single function to import** when integrating this service
    into a larger project.

    Parameters
    ----------
    pdf_path : str
        Path to the Munir Khanani broker statement PDF.
    output_json_path : str, optional
        If provided, the resulting JSON is written to this path as a
        side-effect. The list is always returned regardless.

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
    RuntimeError
        A PSX sector lookup fails after retries.
    """
    logger.info("=== PSX Statement Parser: starting ===")
    logger.info("Input: %s", pdf_path)

    # Step 1 – extract raw rows from PDF
    transactions = extract_transactions(pdf_path)

    # Step 2 – validate each row
    for tx in transactions:
        validate_transaction(tx)

    # Step 3 – deduplicate (removes rows from double API submissions)
    transactions = _check_duplicates(transactions)

    # Step 4 – fetch & attach PSX sectors
    _enrich_with_sectors(transactions)

    # Step 5 – optionally persist to disk
    if output_json_path:
        save_json(transactions, output_json_path)

    logger.info("=== PSX Statement Parser: done (%d records) ===", len(transactions))
    return transactions


# ---------------------------------------------------------------------------
# CLI convenience (python munir_khanani_parser.py statement.pdf [out.json])
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python munir_khanani_parser.py <statement.pdf> [output.json]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else "transactions.json"

    logging.basicConfig(level=logging.INFO)
    result = process_statement(pdf_file, output_json_path=json_file)
    print(json.dumps(result[:3], indent=2, default=str))  # preview first 3 rows
    print(f"\n… {len(result)} total rows written to {json_file}")
