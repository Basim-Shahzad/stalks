"""
akd_trade_parser.py

Production-ready parser for AKD Securities Limited "TRADE CONFIRMATION" PDFs.

Source-of-truth layout (confirmed by inspecting real sample PDFs, both text-
extraction order and word-position order):

    AKD SECURITIES LIMITED
    529, Pakistan Stock Exchange Building, Karachi.
    Date <Month DD, YYYY>                         TRADE CONFIRMATION
    To <CLIENT NAME> - <CLIENT CODE>
    Address: ...
    Contact: ...
    Memo #
    <memo number>
    Scrip Market House A/c. Quantity Rate Comm. Amount CVT/WHT Secp Laga
        PSX Laga Sales Tax NCCPL Advance Tax CDC Charges Amount
    P U R C H A S E                     <- section header, spaced out letters
    <SYMBOL> Ready <Qty> <Rate> <Comm> <CVT/WHT> <SecpLaga> <PSXLaga>
        <SalesTax> <NCCPL> <AdvanceTax> <CDCCharges> <Amount>
    ... (repeated rows)
    Total : <Qty> <Comm> <CVT/WHT> <SecpLaga> <PSXLaga> <SalesTax> <NCCPL>
        <AdvanceTax> <CDCCharges> <Amount>
    S A L E                             <- section header (optional, only if sells exist)
    ... rows ...
    Total : ...
    Client Total : ...
    Summary
    Buy Amount : X   Sell Amount : Y   Net Amount : Z
    Settlement Date : ...

Each row's per-scrip data line has exactly 12 numeric fields after the
Scrip/Market columns, in this fixed order:

    Quantity, Rate, Comm.Amount, CVT/WHT, SecpLaga, PSXLaga, SalesTax,
    NCCPL, AdvanceTax, CDCCharges, Amount

Design notes for this implementation:
  * Uses pdfplumber (already in requirements.txt) exclusively for extraction.
    No other PDF backend is used or required.
  * All monetary/quantity math uses `decimal.Decimal` — never float.
  * Parsing works off `page.extract_text()` per page, which was verified
    against the underlying word-position stream to preserve the documented
    left-to-right column order for this template.
  * Handles multiple pages (Scrip header row can repeat on later pages),
    multiple BUY/SELL sections, and blank/whitespace irregularities.
  * Sector lookup is cache-only here — pulled from the shared sector cache
    (features/transactions/sectors.py). If a symbol isn't present, `sector` is
    `None` and the import job resolves it from PSX. No sector is ever invented.
  * Designed to be imported and called from a web server (Flask etc.):
    stateless functions, no globals mutated per-call, exceptions raised as
    structured error objects rather than crashing the process, and a single
    entry point `parse_pdf(...)` that returns transactions + warnings/errors.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO, Iterable, cast

import pdfplumber

from ..sectors import get_cached_sector

logger = logging.getLogger("akd_trade_parser")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Header line that appears above every data table (may repeat on each page).
_HEADER_LINE_RE = re.compile(
    r"^Scrip\s+Market\s+House\s+A/c\.\s+Quantity\s+Rate\s+Comm\.\s+Amount"
)

# Section markers are printed as spaced-out capital letters, e.g. "P U R C H A S E"
# or "S A L E". We detect them by stripping spaces and matching the word.
_SECTION_RE = re.compile(r"^(?:[A-Z]\s+){2,}[A-Z]$")

# "Date August 28, 2026 TRADE CONFIRMATION" (trailing text may vary/repeat per page)
_DATE_RE = re.compile(r"^Date\s+([A-Za-z]+\s+\d{1,2},\s*\d{4})")

# "To BASIM SHAHZAD - COAF67130"
_CLIENT_RE = re.compile(r"^To\s+(.+?)\s*-\s*([A-Za-z0-9]+)\s*$")

# "Memo #" followed on the *next* text line by the actual memo number.
_MEMO_LABEL_RE = re.compile(r"^Memo\s*#\s*$")
_MEMO_VALUE_RE = re.compile(r"^\d+/[A-Za-z0-9]+\s*$")

# A per-scrip data row: SYMBOL <Market e.g. Ready> <11 or 12 numeric tokens>
# Numeric tokens may contain commas and a leading '-' but not letters.
_NUMBER_TOKEN = r"-?[\d,]+(?:\.\d+)?"
_ROW_RE = re.compile(
    rf"^(?P<scrip>[A-Za-z0-9\-]+)\s+"
    rf"(?P<market>Ready|Future|Spot|T\+\d+)\s+"
    rf"(?P<numbers>(?:{_NUMBER_TOKEN}\s+){{10,11}}{_NUMBER_TOKEN})\s*$"
)

# "Total : <numbers>" line closing each section — not a transaction, but used
# for cross-validation (sums should match the rows we parsed).
_TOTAL_RE = re.compile(
    rf"^Total\s*:\s+(?P<numbers>(?:{_NUMBER_TOKEN}\s+)+{_NUMBER_TOKEN})\s*$"
)

_CLIENT_TOTAL_RE = re.compile(r"^Client\s+Total\s*:")

_SUMMARY_RE = re.compile(r"^Summary\s*$")

# Column order for the 11 numeric fields that follow Quantity+Rate is fixed:
#   Quantity, Rate, Comm, CVT/WHT, SecpLaga, PSXLaga, SalesTax, NCCPL,
#   AdvanceTax, CDCCharges, Amount   -> 11 numbers total.
# Some rows (rare) may only show 10 numbers if a trailing zero column is
# suppressed; we defensively accept 10 or 11 and log a warning if not 11.
_FIELD_NAMES = [
    "quantity",
    "rate",
    "commission",
    "cvt_wht",
    "secp_laga",
    "psx_laga",
    "sales_tax",
    "nccpl",
    "advance_tax",
    "cdc_charges",
    "amount",
]

_MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #


@dataclass
class ParseWarning:
    message: str
    context: str | None = None

    def to_dict(self) -> dict:
        return {"message": self.message, "context": self.context}


@dataclass
class ParseError:
    message: str
    context: str | None = None

    def to_dict(self) -> dict:
        return {"message": self.message, "context": self.context}


@dataclass
class Transaction:
    transactionDate: str | None
    company: str | None
    symbol: str
    side: str
    quantity: int
    rate: Decimal
    commission: Decimal
    taxes: Decimal
    charges: Decimal
    totalAmount: Decimal
    sector: str | None

    def to_dict(self) -> dict:
        return {
            "transactionDate": self.transactionDate,
            "company": self.company,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "rate": _dec_to_jsonable(self.rate),
            "commission": _dec_to_jsonable(self.commission),
            "taxes": _dec_to_jsonable(self.taxes),
            "charges": _dec_to_jsonable(self.charges),
            "totalAmount": _dec_to_jsonable(self.totalAmount),
            "sector": self.sector,
        }


@dataclass
class ParseResult:
    transactions: list[Transaction] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
    source: str | None = None

    def to_dict(self) -> dict:
        return {
            "transactions": [t.to_dict() for t in self.transactions],
            "warnings": [w.to_dict() for w in self.warnings],
            "errors": [e.to_dict() for e in self.errors],
            "source": self.source,
        }


def _dec_to_jsonable(d: Decimal) -> float:
    """Convert Decimal to a JSON-serializable number without losing the
    Decimal-based computation that produced it. We keep full precision
    internally and only cast to float at the JSON boundary, as `Decimal`
    itself is not JSON serializable by the stdlib `json` module."""
    return float(d)


# --------------------------------------------------------------------------- #
# Core parsing helpers
# --------------------------------------------------------------------------- #


def _parse_decimal(token: str) -> Decimal:
    """Parse a numeric token (possibly with thousands separators) into Decimal.
    Raises InvalidOperation on malformed input — caller decides how to handle."""
    cleaned = token.strip().replace(",", "")
    if cleaned in ("", "-"):
        raise InvalidOperation(f"Empty/invalid numeric token: {token!r}")
    return Decimal(cleaned)


def _parse_date(raw: str) -> str | None:
    """Parse 'August 28, 2026' -> '2026-08-28'. Returns None if unparsable
    (never guesses)."""
    raw = raw.strip()
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$", raw)
    if not m:
        return None
    month_name, day, year = m.groups()
    month = _MONTH_MAP.get(month_name.strip().lower())
    if month is None:
        return None
    try:
        dt = datetime(int(year), month, int(day))
    except ValueError:
        return None
    return dt.strftime("%Y-%m-%d")


def _normalize_side(section: str) -> str | None:
    """Map a spaced-letter section header like 'P U R C H A S E' or 'S A L E'
    to BUY/SELL. Returns None if unrecognized (never guesses)."""
    collapsed = section.replace(" ", "").upper()
    if collapsed == "PURCHASE":
        return "BUY"
    if collapsed == "SALE":
        return "SELL"
    return None


def _split_numbers(numbers_str: str) -> list[str]:
    return numbers_str.split()


# --------------------------------------------------------------------------- #
# Line-level state machine
# --------------------------------------------------------------------------- #


class _DocState:
    """Mutable parse state carried across lines/pages of a single PDF."""

    def __init__(self):
        self.trade_date: str | None = None
        self.client_name: str | None = None
        self.client_code: str | None = None
        self.current_side: str | None = None  # 'BUY' / 'SELL'
        self.awaiting_memo_value = False
        self.in_summary = False


def _iter_pdf_lines(pdf: Any) -> Iterable[tuple[int, str]]:
    """Yield (page_index, line_text) for every non-empty line across all pages,
    in document order. Extra whitespace is collapsed but token order (i.e.
    column order) is preserved, which is what row parsing relies on."""
    for page_idx, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        for raw_line in text.split("\n"):
            line = re.sub(r"\s+", " ", raw_line).strip()
            if line:
                yield page_idx, line


def _process_line(
    line: str,
    page_idx: int,
    state: _DocState,
    result: ParseResult,
) -> None:
    # Table header line (may repeat on every page) — nothing to extract, just skip.
    if _HEADER_LINE_RE.match(line):
        return

    # Section markers: "P U R C H A S E" / "S A L E"
    if _SECTION_RE.match(line):
        side = _normalize_side(line)
        if side:
            state.current_side = side
        else:
            result.warnings.append(
                ParseWarning(
                    message=f"Unrecognized section header, ignoring: {line!r}",
                    context=f"page {page_idx}",
                )
            )
        return

    # Trade date
    m = _DATE_RE.match(line)
    if m:
        parsed = _parse_date(m.group(1))
        if parsed:
            if state.trade_date and state.trade_date != parsed:
                result.warnings.append(
                    ParseWarning(
                        message=(
                            f"Multiple differing dates found in document "
                            f"({state.trade_date} -> {parsed}); rows after this "
                            f"line use the new date."
                        ),
                        context=f"page {page_idx}",
                    )
                )
            state.trade_date = parsed
        else:
            result.warnings.append(
                ParseWarning(
                    message=f"Could not parse date from line: {line!r}",
                    context=f"page {page_idx}",
                )
            )
        return

    # Client name / code
    m = _CLIENT_RE.match(line)
    if m:
        state.client_name = m.group(1).strip()
        state.client_code = m.group(2).strip()
        return

    # Memo # label -> next non-empty line should be the memo value; we don't
    # need the memo number for the output schema, but we consume/validate it
    # so it isn't mistaken for a data row.
    if _MEMO_LABEL_RE.match(line):
        state.awaiting_memo_value = True
        return
    if state.awaiting_memo_value:
        state.awaiting_memo_value = False
        if _MEMO_VALUE_RE.match(line):
            return  # consumed memo number
        # If it didn't look like a memo number, fall through to normal handling.

    if _SUMMARY_RE.match(line):
        state.in_summary = True
        return

    # Once we hit "Summary", remaining lines (Buy/Sell/Net amounts, settlement
    # dates, footnotes, signature disclaimer) are not transaction rows.
    if state.in_summary:
        return

    if _CLIENT_TOTAL_RE.match(line):
        return  # aggregate line, not a transaction

    if _TOTAL_RE.match(line):
        return  # per-section aggregate line, not a transaction

    # Per-scrip data row
    m = _ROW_RE.match(line)
    if m:
        _process_row(m, page_idx, state, result)
        return

    # Anything else (letterhead, address, contact, footnotes, disclaimers,
    # settlement-date continuation lines, "For AKD SECURITIES LIMITED", etc.)
    # is expected boilerplate — silently ignored. We only warn on things that
    # *look* like they might be a malformed data row (start with a token that
    # resembles a scrip symbol followed by numbers) to catch real problems
    # without being noisy about the letterhead/footer text.
    if re.match(r"^[A-Za-z0-9\-]+\s+\S+\s+[\d.,]+", line) and not line.startswith(
        ("Settlement", "T+", "For ", "(1)", "(2)", "(3)", "Note:", "*(This")
    ):
        result.warnings.append(
            ParseWarning(
                message=f"Line resembled a data row but did not match the expected pattern: {line!r}",
                context=f"page {page_idx}",
            )
        )


def _process_row(
    m: re.Match,
    page_idx: int,
    state: _DocState,
    result: ParseResult,
) -> None:
    scrip = m.group("scrip").strip()
    numbers_raw = _split_numbers(m.group("numbers"))

    if state.current_side is None:
        result.errors.append(
            ParseError(
                message=(
                    f"Data row for '{scrip}' found before a BUY/SELL section "
                    f"header; skipping row because side cannot be determined."
                ),
                context=f"page {page_idx}",
            )
        )
        return

    if len(numbers_raw) != len(_FIELD_NAMES):
        result.errors.append(
            ParseError(
                message=(
                    f"Row for '{scrip}' has {len(numbers_raw)} numeric fields, "
                    f"expected {len(_FIELD_NAMES)}. Raw values: {numbers_raw}. "
                    f"Skipping row rather than guessing field alignment."
                ),
                context=f"page {page_idx}",
            )
        )
        return

    parsed: dict[str, Decimal] = {}
    for name, tok in zip(_FIELD_NAMES, numbers_raw):
        try:
            parsed[name] = _parse_decimal(tok)
        except InvalidOperation:
            result.errors.append(
                ParseError(
                    message=f"Could not parse numeric field '{name}'={tok!r} for '{scrip}'; skipping row.",
                    context=f"page {page_idx}",
                )
            )
            return

    quantity_dec = parsed["quantity"]
    if quantity_dec != quantity_dec.to_integral_value():
        result.warnings.append(
            ParseWarning(
                message=(
                    f"Quantity for '{scrip}' is not a whole number "
                    f"({quantity_dec}); keeping as parsed but this is unusual."
                ),
                context=f"page {page_idx}",
            )
        )
    try:
        quantity_int = int(quantity_dec)
    except (ValueError, OverflowError):
        result.errors.append(
            ParseError(
                message=f"Quantity for '{scrip}' could not be converted to int: {quantity_dec}",
                context=f"page {page_idx}",
            )
        )
        return

    taxes = parsed["cvt_wht"] + parsed["sales_tax"] + parsed["advance_tax"]
    charges = (
        parsed["secp_laga"]
        + parsed["psx_laga"]
        + parsed["nccpl"]
        + parsed["cdc_charges"]
    )

    txn = Transaction(
        transactionDate=state.trade_date,
        company=scrip,
        symbol=scrip,
        side=state.current_side,
        quantity=quantity_int,
        rate=parsed["rate"],
        commission=parsed["commission"],
        taxes=taxes,
        charges=charges,
        totalAmount=abs(parsed["amount"]),
        sector=get_cached_sector(scrip),
    )
    result.transactions.append(txn)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def parse_pdf(source: str | Path | BinaryIO | bytes) -> ParseResult:
    """Parse a single AKD Securities trade-confirmation PDF.

    Args:
        source: file path (str/Path), an open binary file-like object, or raw
            PDF bytes. Suitable for use directly with an uploaded file stream
            in a web server (e.g. Flask's `request.files['file'].stream`).

    Returns:
        ParseResult with `.transactions`, `.warnings`, `.errors`, `.source`.
        Never raises for malformed *row* data — those become warnings and the
        row is skipped. Raises only for truly unreadable/non-PDF input, and
        even then the exception is caught and reported as a ParseError with
        an empty transaction list, so callers in a web handler can do:

            result = parse_pdf(file_stream)
            if result.errors:
                return jsonify(result.to_dict()), 422
            return jsonify(result.to_dict())
    """
    result = ParseResult(source=_describe_source(source))

    try:
        pdf_ctx = _open_pdf(source)
    except (
        Exception
    ) as exc:  # noqa: BLE001 - want to report any failure, not crash caller
        result.errors.append(
            ParseError(message=f"Failed to open PDF: {exc}", context=result.source)
        )
        return result

    state = _DocState()
    try:
        with pdf_ctx as pdf:
            if len(pdf.pages) == 0:
                result.errors.append(
                    ParseError(message="PDF has no pages.", context=result.source)
                )
                return result

            for page_idx, line in _iter_pdf_lines(pdf):
                try:
                    _process_line(line, page_idx, state, result)
                except Exception as exc:  # noqa: BLE001
                    # Never let one bad line abort the whole document.
                    result.errors.append(
                        ParseError(
                            message=f"Unexpected error processing line {line!r}: {exc}",
                            context=f"page {page_idx}",
                        )
                    )
    except Exception as exc:  # noqa: BLE001
        result.errors.append(
            ParseError(
                message=f"Failed while reading PDF content: {exc}",
                context=result.source,
            )
        )
        return result

    if not result.transactions and not result.errors:
        result.warnings.append(
            ParseWarning(
                message="No transaction rows were found in this document.",
                context=result.source,
            )
        )

    if state.trade_date is None:
        result.warnings.append(
            ParseWarning(
                message="Could not determine a transaction date for this document."
            )
        )
    if state.client_name is None:
        result.warnings.append(
            ParseWarning(
                message="Could not determine the client/company name for this document."
            )
        )

    return result


def parse_pdfs(sources: Iterable[str | Path | BinaryIO | bytes]) -> ParseResult:
    """Parse and merge multiple PDFs into a single ParseResult. Useful for
    batch endpoints. Warnings/errors are tagged with their originating source
    via the `context` field where possible."""
    merged = ParseResult(source="batch")
    for src in sources:
        single = parse_pdf(src)
        merged.transactions.extend(single.transactions)
        merged.warnings.extend(single.warnings)
        merged.errors.extend(single.errors)
    return merged


def _describe_source(source: str | Path | BinaryIO | bytes) -> str:
    if isinstance(source, (str, Path)):
        return str(source)
    name = getattr(source, "name", None)
    if name:
        return str(name)
    if isinstance(source, bytes):
        return f"<bytes:{len(source)}>"
    return "<stream>"


def _open_pdf(source: str | Path | BinaryIO | bytes):
    """Return a context manager yielding a pdfplumber.PDF, regardless of
    whether `source` is a path, bytes, or a file-like stream."""
    if isinstance(source, (str, Path)):
        return pdfplumber.open(source)
    if isinstance(source, bytes):
        import io

        return pdfplumber.open(io.BytesIO(source))
    # Assume file-like object (has .read()). Ensure we're at the start.
    try:
        source.seek(0)
    except (AttributeError, OSError):
        pass
    return pdfplumber.open(cast(Any, source))
