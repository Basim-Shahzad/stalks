"""
Shared PSX sector lookup used by every statement parser and by manual
transaction entry.

Symbol -> sector mappings are cached in memory and persisted to a single JSON
file (``core/data/cache/sector_cache.json``). Missing symbols are resolved
from the PSX company page.
"""

from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from core.logger import logger

PSX_SECTORS = [
    "AUTOMOBILE ASSEMBLER",
    "AUTOMOBILE PARTS & ACCESSORIES",
    "CABLE & ELECTRICAL GOODS",
    "CEMENT",
    "CHEMICAL",
    "CLOSE - END MUTUAL FUND",
    "COMMERCIAL BANKS",
    "ENGINEERING",
    "EXCHANGE TRADED FUNDS",
    "FERTILIZER",
    "FOOD & PERSONAL CARE PRODUCTS",
    "GLASS & CERAMICS",
    "INV. BANKS / INV. COS. / SECURITIES COS.",
    "INSURANCE",
    "JUTE",
    "LEATHER & TANNERIES",
    "LEASING COMPANIES",
    "MISCELLANEOUS",
    "MODARABAS",
    "OIL & GAS EXPLORATION COMPANIES",
    "OIL & GAS MARKETING COMPANIES",
    "PAPER, BOARD & PACKAGING",
    "PHARMACEUTICALS",
    "POWER GENERATION & DISTRIBUTION",
    "PROPERTY",
    "REAL ESTATE INVESTMENT AND SERVICES",
    "REAL ESTATE INVESTMENT TRUST",
    "REFINERY",
    "SUGAR & ALLIED INDUSTRIES",
    "SYNTHETIC & RAYON",
    "TECHNOLOGY & COMMUNICATION",
    "TEXTILE COMPOSITE",
    "TEXTILE SPINNING",
    "TEXTILE WEAVING",
    "TOBACCO",
    "TRANSPORT",
    "VANASPATI & ALLIED INDUSTRIES",
    "WOOLLEN",
]

# features/transactions/sectors.py -> features/transactions -> features -> server
SECTOR_CACHE_FILE = (
    Path(__file__).resolve().parents[2] / "core" / "data" / "cache" / "sector_cache.json"
)

_MAX_CONCURRENT_LOOKUPS = 5
_MAX_ATTEMPTS = 3

_SECTOR_CACHE: dict[str, str] = {}
_cache_loaded = False


class SectorNotFoundError(LookupError):
    """The symbol does not exist on PSX, or its sector could not be matched."""


class SectorFetchError(RuntimeError):
    """The PSX page could not be fetched (network / HTTP failure)."""


def _ensure_loaded() -> None:
    """Lazily load the on-disk cache (no import-time I/O)."""
    global _SECTOR_CACHE, _cache_loaded
    if _cache_loaded:
        return
    _cache_loaded = True
    if SECTOR_CACHE_FILE.exists():
        try:
            raw = json.loads(SECTOR_CACHE_FILE.read_text(encoding="utf-8"))
            _SECTOR_CACHE = {str(k).upper(): v for k, v in raw.items()}
            logger.info("Sector cache loaded: %d symbols", len(_SECTOR_CACHE))
        except (json.JSONDecodeError, OSError, AttributeError) as e:
            logger.warning("Could not load sector cache: %s — starting fresh", e)
            _SECTOR_CACHE = {}


def get_cached_sector(symbol: str) -> str | None:
    """Return the cached sector for ``symbol`` or None. Never does I/O after the
    first call."""
    _ensure_loaded()
    return _SECTOR_CACHE.get(symbol.strip().upper())


async def _save_cache() -> None:
    """Persist the in-memory cache without blocking the event loop."""
    snapshot = json.dumps(_SECTOR_CACHE, indent=2, ensure_ascii=False, sort_keys=True)

    def _write() -> None:
        try:
            SECTOR_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp = SECTOR_CACHE_FILE.with_suffix(".tmp")
            tmp.write_text(snapshot, encoding="utf-8")
            tmp.replace(SECTOR_CACHE_FILE)  # atomic swap
        except OSError as e:
            logger.warning("Could not save sector cache: %s", e)

    await asyncio.to_thread(_write)


def _normalize(s: str) -> str:
    """Punctuation/whitespace-insensitive form used for fuzzy comparison."""
    s = unicodedata.normalize("NFKD", s).upper()
    s = re.sub(r"[^A-Z0-9\s]", "", s)
    return re.sub(r"\s+", "", s)


_SECTOR_NORM_MAP: dict[str, str] = {_normalize(s): s for s in PSX_SECTORS}


def _match_sector(soup: BeautifulSoup) -> str | None:
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
                return canonical

    # Tier 2: normalized match (punctuation/whitespace insensitive)
    for text in candidates:
        canonical = _SECTOR_NORM_MAP.get(_normalize(text))
        if canonical:
            return canonical

    # Tier 3: substring against full page text, accepted only when exactly one
    # sector name appears — otherwise it is ambiguous and we refuse to guess.
    full_page_norm = _normalize(soup.get_text())
    hits = [c for n, c in _SECTOR_NORM_MAP.items() if n in full_page_norm]
    if len(hits) == 1:
        logger.warning("Sector matched by unique substring fallback: %s", hits[0])
        return hits[0]
    return None


async def _fetch_sector(client: httpx.AsyncClient, symbol: str) -> str:
    url = f"https://dps.psx.com.pk/company/{symbol}"
    last_error: Exception | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                raise SectorNotFoundError(f"Symbol {symbol!r} not found on PSX")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            last_error = exc
            logger.warning(
                "PSX lookup attempt %d/%d failed for %s: %s",
                attempt,
                _MAX_ATTEMPTS,
                symbol,
                exc,
            )
            if attempt < _MAX_ATTEMPTS:
                await asyncio.sleep(2 * attempt)
            continue

        sector = _match_sector(BeautifulSoup(resp.text, "html.parser"))
        if sector is None:
            raise SectorNotFoundError(f"Sector not found in PSX page for {symbol!r}")
        return sector

    raise SectorFetchError(
        f"Failed to fetch PSX sector for {symbol!r} after {_MAX_ATTEMPTS} attempts. "
        f"Last error: {last_error}"
    )


async def resolve_sectors(symbols: list[str]) -> dict[str, str]:
    """Resolve sectors for ``symbols`` (cache first, then PSX).

    Lookups share one HTTP client and are bounded by a semaphore. The cache is
    written once at the end, including partial successes. If any symbol fails,
    raises after the cache is saved so a retry only repeats the failures.
    """
    _ensure_loaded()
    wanted = sorted({s.strip().upper() for s in symbols if s and s.strip()})
    result = {s: _SECTOR_CACHE[s] for s in wanted if s in _SECTOR_CACHE}
    missing = [s for s in wanted if s not in result]
    if not missing:
        return result

    logger.info("Fetching sectors for %d unique symbols…", len(missing))
    sem = asyncio.Semaphore(_MAX_CONCURRENT_LOOKUPS)

    async with httpx.AsyncClient(timeout=15.0) as client:

        async def _one(sym: str) -> str:
            async with sem:
                return await _fetch_sector(client, sym)

        outcomes = await asyncio.gather(
            *[_one(s) for s in missing], return_exceptions=True
        )

    failures: list[str] = []
    not_found: list[str] = []
    for sym, outcome in zip(missing, outcomes):
        if isinstance(outcome, SectorNotFoundError):
            not_found.append(sym)
        elif isinstance(outcome, BaseException):
            failures.append(f"{sym} ({outcome})")
        else:
            _SECTOR_CACHE[sym] = outcome
            result[sym] = outcome

    if len(result) > len(wanted) - len(missing):
        await _save_cache()

    if not_found:
        raise SectorNotFoundError(
            "Unknown symbol(s) or sector not found on PSX: " + ", ".join(not_found)
        )
    if failures:
        raise SectorFetchError("Sector lookup failed for: " + "; ".join(failures))
    return result


async def get_psx_sector(symbol: str) -> str:
    """Single-symbol convenience wrapper around :func:`resolve_sectors`."""
    sym = symbol.strip().upper()
    return (await resolve_sectors([sym]))[sym]


async def enrich_with_sectors(transactions: list[dict]) -> list[dict]:
    """Add a 'sector' key to every transaction dict (mutates and returns it)."""
    sector_map = await resolve_sectors([t["symbol"] for t in transactions])
    for tx in transactions:
        tx["sector"] = sector_map[tx["symbol"].strip().upper()]
    return transactions
