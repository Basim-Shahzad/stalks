from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from features.transactions.models.Transaction import Transaction
    from services.psx_service import PSXScraperService


TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")

_BUY_TOKENS = {"BUY", "SIDE.BUY", "B"}
_SELL_TOKENS = {"SELL", "SIDE.SELL", "S"}


class TransactionSideError(ValueError):
    """Raised when a transaction's side cannot be classified as BUY or SELL."""


class OversellError(ValueError):
    """Raised when a SELL transaction's quantity exceeds the open lots for that symbol."""


def _classify_side(side) -> bool:
    """
    Returns True for BUY, False for SELL.
    Raises TransactionSideError for anything unrecognized instead of
    silently defaulting to SELL (which would corrupt P&L on bad data).
    """
    token = str(side).upper()
    if token in _BUY_TOKENS:
        return True
    if token in _SELL_TOKENS:
        return False
    raise TransactionSideError(f"Unrecognized transaction side: {side!r}")


@dataclass
class Holding:
    symbol: str
    company: str
    sector: str

    # Position
    quantity: Decimal
    avg_cost: Decimal
    total_invested: Decimal
    total_fees: Decimal

    # Live market data (populated after fetch)
    current_price: Decimal = Decimal("0")
    ldcp: Decimal = Decimal("0")
    day_change: Decimal = Decimal("0")
    day_change_pct: Decimal = Decimal("0")
    direction: str = ""
    has_market_data: bool = False  # True only once _enrich successfully populates this symbol

    # Realised P&L
    realised_pnl: Decimal = field(default=Decimal("0"))

    @property
    def market_value(self) -> Decimal:
        return (self.quantity * self.current_price).quantize(TWO_PLACES)

    @property
    def cost_basis(self) -> Decimal:
        return (self.quantity * self.avg_cost).quantize(TWO_PLACES)

    @property
    def unrealised_pnl(self) -> Decimal:
        if not self.has_market_data:
            return Decimal("0")
        return (self.market_value - self.cost_basis).quantize(TWO_PLACES)

    @property
    def unrealised_pnl_pct(self) -> Decimal:
        if not self.has_market_data or self.cost_basis == 0:
            return Decimal("0")
        return ((self.unrealised_pnl / self.cost_basis) * 100).quantize(TWO_PLACES)

    @property
    def total_pnl(self) -> Decimal:
        return (self.unrealised_pnl + self.realised_pnl).quantize(TWO_PLACES)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "company": self.company,
            "sector": self.sector,
            "quantity": str(self.quantity),
            "avg_cost": str(self.avg_cost),
            "total_invested": str(self.total_invested),
            "total_fees": str(self.total_fees),
            "current_price": str(self.current_price),
            "ldcp": str(self.ldcp),
            "day_change": str(self.day_change),
            "day_change_pct": str(self.day_change_pct),
            "direction": self.direction,
            "has_market_data": self.has_market_data,
            "market_value": str(self.market_value),
            "cost_basis": str(self.cost_basis),
            "unrealised_pnl": str(self.unrealised_pnl),
            "unrealised_pnl_pct": str(self.unrealised_pnl_pct),
            "realised_pnl": str(self.realised_pnl),
            "total_pnl": str(self.total_pnl),
        }


@dataclass
class HoldingsSummary:
    total_invested: Decimal
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_fees: Decimal
    total_unrealised_pnl: Decimal
    total_realised_pnl: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    holdings_count: int
    holdings_with_market_data: int

    def to_dict(self) -> dict:
        return {
            "total_invested": str(self.total_invested),
            "total_market_value": str(self.total_market_value),
            "total_cost_basis": str(self.total_cost_basis),
            "total_fees": str(self.total_fees),
            "total_unrealised_pnl": str(self.total_unrealised_pnl),
            "total_realised_pnl": str(self.total_realised_pnl),
            "total_pnl": str(self.total_pnl),
            "total_pnl_pct": str(self.total_pnl_pct),
            "holdings_count": self.holdings_count,
            "holdings_with_market_data": self.holdings_with_market_data,
        }


class Holdings:
    def __init__(self) -> None:
        self._holdings: dict[str, Holding] = {}
        # Lifetime accumulators across ALL symbols ever traded, including
        # ones fully closed out (no open quantity remaining). self._holdings
        # only contains symbols with open_qty > 0, so these are tracked
        # separately to avoid silently dropping the invested capital, fees,
        # and realised P&L of every closed-out position from the summary.
        self._lifetime_invested: Decimal = Decimal("0")
        self._lifetime_fees: Decimal = Decimal("0")
        self._lifetime_realised_pnl: Decimal = Decimal("0")

    # ------------------------------------------------------------------ #
    #  Factory                                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_transactions(
        cls,
        transactions: list["Transaction"],
        psx: "PSXScraperService",
    ) -> "Holdings":
        instance = cls()
        instance._build(transactions)
        if instance._holdings:
            instance._enrich(psx)
        return instance

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @property
    def holdings(self) -> list[Holding]:
        return list(self._holdings.values())

    @property
    def summary(self) -> HoldingsSummary:
        items = self.holdings

        # Open-position figures (market value, cost basis, unrealised P&L)
        # only make sense for symbols you currently hold, so those still
        # come from self.holdings.
        total_market_value = sum((h.market_value for h in items), Decimal("0"))
        total_cost_basis = sum((h.cost_basis for h in items), Decimal("0"))
        total_unrealised = sum((h.unrealised_pnl for h in items), Decimal("0"))

        # Invested capital, fees, and realised P&L are lifetime figures —
        # they must include closed-out positions too, or a fully round-
        # tripped trade (bought and later fully sold) vanishes from the
        # summary entirely even though it affected your actual P&L and cash
        # flow. Use the running lifetime accumulators instead of re-deriving
        # from self.holdings, which only contains open positions.
        total_invested = self._lifetime_invested
        total_fees = self._lifetime_fees
        total_realised = self._lifetime_realised_pnl

        total_pnl = total_unrealised + total_realised
        total_pnl_pct = (
            (total_pnl / total_cost_basis * 100).quantize(TWO_PLACES)
            if total_cost_basis
            else Decimal("0")
        )
        return HoldingsSummary(
            total_invested=total_invested.quantize(TWO_PLACES),
            total_market_value=total_market_value.quantize(TWO_PLACES),
            total_cost_basis=total_cost_basis.quantize(TWO_PLACES),
            total_fees=total_fees.quantize(TWO_PLACES),
            total_unrealised_pnl=total_unrealised.quantize(TWO_PLACES),
            total_realised_pnl=total_realised.quantize(TWO_PLACES),
            total_pnl=total_pnl.quantize(TWO_PLACES),
            total_pnl_pct=total_pnl_pct,
            holdings_count=len(items),
            holdings_with_market_data=sum(1 for h in items if h.has_market_data),
        )

    def to_dict(self) -> dict:
        return {
            "holdings": [h.to_dict() for h in self.holdings],
            "summary": self.summary.to_dict(),
        }

    # ------------------------------------------------------------------ #
    #  Internal: build from transactions (pure, sync)                     #
    # ------------------------------------------------------------------ #

    def _build(self, transactions: list["Transaction"]) -> None:
        """
        Runs FIFO lot accounting over the full transaction history.

        Ordering: transactions are sorted by (transaction_date, id) where
        available, so that same-day trades resolve deterministically rather
        than relying on incoming list order. Falls back to date-only if the
        transaction has no id/sequence attribute.
        """
        lots: dict[str, list[list[Decimal]]] = defaultdict(list)
        meta: dict[str, dict] = {}
        total_invested: dict[str, Decimal] = defaultdict(Decimal)
        total_fees: dict[str, Decimal] = defaultdict(Decimal)
        realised_pnl: dict[str, Decimal] = defaultdict(Decimal)

        def sort_key(t: "Transaction"):
            # No intraday timestamps are available from the data source, so
            # true same-day ordering is unknowable. Rather than sort by a
            # random id (which can put a SELL before its same-day BUY and
            # trigger a spurious OversellError), we apply a deliberate
            # convention: on a tied date, all BUYs settle before all SELLs.
            # This is the only interpretation of "same day" that can't
            # produce an impossible state.
            is_buy = _classify_side(t.side)
            side_rank = 0 if is_buy else 1
            return (t.transaction_date, side_rank)

        sorted_txns = sorted(transactions, key=sort_key)

        for txn in sorted_txns:
            sym = txn.symbol
            qty = txn.quantity
            fees = txn.commission + txn.taxes + txn.charges

            if qty is None or qty <= 0:
                raise ValueError(f"Transaction for {sym} has invalid quantity: {qty!r}")

            is_buy = _classify_side(txn.side)

            meta[sym] = {"company": txn.company, "sector": txn.sector or ""}
            total_fees[sym] += fees

            if is_buy:
                # Cost per share is based on total_amount (assumed to include
                # fees, i.e. the actual cash outlay), kept at 4dp for accumulation
                # precision, then rounded only at presentation time.
                cost_per_share = (txn.total_amount / qty).quantize(FOUR_PLACES)
                lots[sym].append([qty, cost_per_share])
                total_invested[sym] += txn.total_amount

            else:  # SELL
                sell_qty = qty
                proceeds_per_share = (txn.total_amount / qty).quantize(FOUR_PLACES)

                while sell_qty > 0 and lots[sym]:
                    lot_qty, lot_cost = lots[sym][0]
                    consumed = min(sell_qty, lot_qty)

                    realised_pnl[sym] += (
                        consumed * (proceeds_per_share - lot_cost)
                    ).quantize(FOUR_PLACES)

                    if consumed >= lot_qty:
                        lots[sym].pop(0)
                    else:
                        lots[sym][0][0] -= consumed

                    sell_qty -= consumed

                if sell_qty > 0:
                    # Previously this was silently swallowed. That's dangerous
                    # for financial data — surface it loudly instead.
                    raise OversellError(
                        f"Sell of {qty} {sym} on {txn.transaction_date} exceeds "
                        f"open lots by {sell_qty}. Check for missing buy "
                        f"transactions or bad data."
                    )

        # Lifetime accumulators must be summed from the per-symbol dicts
        # (which cover every symbol ever traded), not derived from
        # self._holdings below, which only contains symbols with an open
        # position and would silently drop closed-out trades.
        self._lifetime_invested = sum(total_invested.values(), Decimal("0"))
        self._lifetime_fees = sum(total_fees.values(), Decimal("0"))
        self._lifetime_realised_pnl = sum(realised_pnl.values(), Decimal("0"))

        for sym, sym_lots in lots.items():
            if not sym_lots:
                continue

            open_qty = sum(l[0] for l in sym_lots)
            if open_qty <= 0:
                continue

            avg_cost = (sum(l[0] * l[1] for l in sym_lots) / open_qty).quantize(
                FOUR_PLACES
            )

            self._holdings[sym] = Holding(
                symbol=sym,
                company=meta[sym]["company"],
                sector=meta[sym]["sector"],
                quantity=open_qty,
                avg_cost=avg_cost,
                total_invested=total_invested[sym].quantize(TWO_PLACES),
                total_fees=total_fees[sym].quantize(TWO_PLACES),
                realised_pnl=realised_pnl[sym].quantize(TWO_PLACES),
            )

    # ------------------------------------------------------------------ #
    #  Internal: enrich with live market data (sync)                      #
    # ------------------------------------------------------------------ #

    def _enrich(self, psx: "PSXScraperService") -> None:
        symbols = list(self._holdings.keys())
        if not symbols:
            return

        market_data: list[dict] = psx.get_market_data(symbols)

        for item in market_data:
            sym = item.get("symbol")
            if sym not in self._holdings:
                continue
            h = self._holdings[sym]
            h.current_price = item.get("current", Decimal("0"))
            h.ldcp = item.get("ldcp", Decimal("0"))
            h.day_change = item.get("change", Decimal("0"))
            h.day_change_pct = item.get("change_pct", Decimal("0"))
            h.direction = item.get("direction", "")
            h.has_market_data = True
        # Symbols not present in market_data keep has_market_data=False,
        # so callers can distinguish "no gain/loss" from "no price fetched."