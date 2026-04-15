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
_CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "cache" / "sector_cache.json"
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

# Header line: "COMPANY FULL NAME SYMBOL"
# e.g.  "ARIF HABIB CORPORATION LTD AHCL"
# The symbol is the LAST whitespace-delimited token (all-caps/digits, 2-10 chars).
# We reject lines that start with a date or contain 'Net '/'Total' to avoid
# false-positive matches on data or summary rows.
_RE_HEADER = re.compile(r"^(.+?)\s+([A-Z][A-Z0-9]{1,9})\s*$")

# Transaction data line (buy or sell)
# e.g.  "26-02-26 AHCL T+1REG B 622 0 16.1000 0.0300 2.80 5.81 10,041.46"
# Note: sell qty and taxes can be 0; amount can be negative (sell rows)
_RE_TX = re.compile(
    r"^(\d{2}-\d{2}-\d{2})\s+"  # date  DD-MM-YY
    r"([A-Z][A-Z0-9]+)\s+"  # symbol
    r"T\+\d+REG\s+"  # settlement (ignored)
    r"([BP])\s+"  # B = buy, P = sell
    r"([\d,]+)\s+"  # buy qty
    r"([\d,]+)\s+"  # sell qty
    r"([\d,]+\.\d+)\s+"  # rate
    r"([\d,]+\.\d+)\s+"  # commission
    r"([\d,]+\.\d+)\s+"  # taxes
    r"([\d,]+\.\d+)\s+"  # charges
    r"(-?[\d,]+\.\d+)\s*$"  # amount
)

# "Net" summary line — used only to confirm we've consumed all rows for a symbol
_RE_NET = re.compile(r"^Net\s+\.")

# Normalise month abbreviations: PDF uses 2-digit year, we need DD-MMM-YY
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


def _reformat_date(raw: str) -> str:
    """
    Convert 'DD-MM-YY' (as in the PDF) to 'DD-MMM-YY'.
    e.g. '26-02-26' → '26-FEB-26'
    Raises ValueError if format is unrecognised.
    """
    parts = raw.split("-")
    if len(parts) != 3 or len(parts[1]) != 2:
        raise ValueError(f"Unexpected date format: {raw!r}")
    month_abbr = _MONTH_MAP.get(parts[1])
    if month_abbr is None:
        raise ValueError(f"Unknown month number in date: {raw!r}")
    return f"{parts[0]}-{month_abbr}-{parts[2]}"


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
    Parse a Munir Khanani broker statement PDF and return a list of
    transaction dicts.

    The parser is line-oriented:
      1. Scans for company header lines → sets current_company / current_symbol
      2. Matches transaction data lines → appends records
      3. Skips Net/summary lines and page boilerplate

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
        If a transaction row cannot be reliably parsed.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    transactions: list[dict] = []
    current_company: Optional[str] = None
    current_symbol: Optional[str] = None

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

                # Skip page-level boilerplate
                if _is_page_header_line(line):
                    continue

                # Skip Net summary rows
                if _RE_NET.match(line):
                    continue

                # Try to match a transaction data row first (most common)
                m_tx = _RE_TX.match(line)
                if m_tx:
                    if current_symbol is None:
                        raise ValueError(
                            f"Found transaction row before any company header: "
                            f"{line!r}"
                        )
                    (
                        raw_date,
                        sym,
                        direction,
                        buy_s,
                        sell_s,
                        rate_s,
                        comm_rate_s,
                        adc_s,
                        svc_charges_s,
                        amount_s,
                    ) = m_tx.groups()

                    # Symbol in row must match current section
                    if sym != current_symbol:
                        raise ValueError(
                            f"Symbol mismatch: row has {sym!r} but current "
                            f"section is {current_symbol!r}. Line: {line!r}"
                        )

                    buy_qty = _parse_number(buy_s)
                    sell_qty = _parse_number(sell_s)
                    qty = buy_qty if buy_qty > 0 else sell_qty

                    # PDF columns:
                    #   Comm.   = per-share commission rate  → actual = qty × rate
                    #   ADC.    = CDC/LAGA/other taxes        → schema: taxes
                    #   Charges = broker service charges      → schema: charges
                    commission = round(qty * _parse_number(comm_rate_s), 2)

                    transactions.append(
                        {
                            "date": _reformat_date(raw_date),
                            "company": current_company,
                            "symbol": current_symbol,
                            "buy": buy_qty,
                            "sell": sell_qty,
                            "rate": _parse_number(rate_s),
                            "commission": commission,
                            "taxes": _parse_number(adc_s),
                            "charges": _parse_number(svc_charges_s),
                            "total_amount": _parse_number(amount_s),
                        }
                    )
                    continue

                # Try to match a company header line
                m_hdr = _RE_HEADER.match(line)
                if m_hdr:
                    candidate_company = m_hdr.group(1).strip()
                    candidate_symbol = m_hdr.group(2).strip()
                    # Guard: reject lines that are data/summary rows mis-matched
                    is_data_row = bool(
                        re.match(r"^\d{2}-\d{2}-\d{2}", candidate_company)
                    )
                    is_summary = (
                        "Net" in candidate_company or "Total" in candidate_company
                    )
                    if not is_data_row and not is_summary:
                        current_company = candidate_company
                        current_symbol = candidate_symbol
                        logger.debug(
                            "  Section: %s  [%s]", current_company, current_symbol
                        )
                        continue

                # Anything else: log at DEBUG and ignore
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


def _check_duplicates(transactions: list[dict]) -> None:
    """
    Log a warning for any rows that are byte-for-byte identical.
    Does NOT remove them — confirmed duplicate trades are valid.
    """
    seen: dict[tuple, int] = {}
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
                "Duplicate detected: row %d is identical to row %d  "
                "(%s %s qty=%s rate=%s). Keeping both.",
                i,
                seen[key],
                tx["date"],
                tx["symbol"],
                tx["buy"] or tx["sell"],
                tx["rate"],
            )
        else:
            seen[key] = i


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------


def save_json(data: list[dict], output_path: str) -> None:
    """
    Write *data* as pretty-printed JSON to *output_path*.

    Parameters
    ----------
    data : list[dict]
        Transaction records as returned by process_statement().
    output_path : str
        Destination file path (will be created or overwritten).
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
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

    # Step 3 – warn on duplicate rows
    _check_duplicates(transactions)

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
    print(json.dumps(result[:3], indent=2))  # preview first 3 rows
    print(f"\n… {len(result)} total rows written to {json_file}")
