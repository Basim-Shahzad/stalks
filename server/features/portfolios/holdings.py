from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from features.transactions.models.Transaction import Transaction
    from services.psx_service import PSXScraperService


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

    # Realised P&L
    realised_pnl: Decimal = field(default=Decimal("0"))

    @property
    def market_value(self) -> Decimal:
        return (self.quantity * self.current_price).quantize(Decimal("0.01"))

    @property
    def cost_basis(self) -> Decimal:
        return (self.quantity * self.avg_cost).quantize(Decimal("0.01"))

    @property
    def unrealised_pnl(self) -> Decimal:
        return (self.market_value - self.cost_basis).quantize(Decimal("0.01"))

    @property
    def unrealised_pnl_pct(self) -> Decimal:
        if self.cost_basis == 0:
            return Decimal("0")
        return ((self.unrealised_pnl / self.cost_basis) * 100).quantize(Decimal("0.01"))

    @property
    def total_pnl(self) -> Decimal:
        return (self.unrealised_pnl + self.realised_pnl).quantize(Decimal("0.01"))

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
        }


class Holdings:
    def __init__(self) -> None:
        self._holdings: dict[str, Holding] = {}

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
        total_invested = sum((h.total_invested for h in items), Decimal("0"))
        total_market_value = sum((h.market_value for h in items), Decimal("0"))
        total_cost_basis = sum((h.cost_basis for h in items), Decimal("0"))
        total_fees = sum((h.total_fees for h in items), Decimal("0"))
        total_unrealised = sum((h.unrealised_pnl for h in items), Decimal("0"))
        total_realised = sum((h.realised_pnl for h in items), Decimal("0"))
        total_pnl = total_unrealised + total_realised
        total_pnl_pct = (
            (total_pnl / total_cost_basis * 100).quantize(Decimal("0.01"))
            if total_cost_basis
            else Decimal("0")
        )
        return HoldingsSummary(
            total_invested=total_invested.quantize(Decimal("0.01")),
            total_market_value=total_market_value.quantize(Decimal("0.01")),
            total_cost_basis=total_cost_basis.quantize(Decimal("0.01")),
            total_fees=total_fees.quantize(Decimal("0.01")),
            total_unrealised_pnl=total_unrealised.quantize(Decimal("0.01")),
            total_realised_pnl=total_realised.quantize(Decimal("0.01")),
            total_pnl=total_pnl.quantize(Decimal("0.01")),
            total_pnl_pct=total_pnl_pct,
            holdings_count=len(items),
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
        def _is_buy(side) -> bool:
            return str(side).upper() in {"BUY", "SIDE.BUY", "B"}

        lots: dict[str, list[list[Decimal]]] = defaultdict(list)

        meta: dict[str, dict] = {}
        total_invested: dict[str, Decimal] = defaultdict(Decimal)
        total_fees: dict[str, Decimal] = defaultdict(Decimal)
        realised_pnl: dict[str, Decimal] = defaultdict(Decimal)

        sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)

        for txn in sorted_txns:
            sym = txn.symbol
            qty = txn.quantity
            rate = txn.rate
            fees = txn.commission + txn.taxes + txn.charges

            meta[sym] = {"company": txn.company, "sector": txn.sector or ""}
            total_fees[sym] += fees

            if _is_buy(txn.side):
                cost_per_share = (txn.total_amount / qty).quantize(Decimal("0.0001"))
                lots[sym].append([qty, cost_per_share])
                total_invested[sym] += txn.total_amount

            else:  # SELL
                sell_qty = qty
                sell_proceeds = txn.total_amount

                while sell_qty > 0 and lots[sym]:
                    lot_qty, lot_cost = lots[sym][0]

                    consumed = min(sell_qty, lot_qty)
                    realised_pnl[sym] += (
                        consumed * (sell_proceeds / qty - lot_cost)
                    ).quantize(Decimal("0.0001"))

                    if consumed >= lot_qty:
                        lots[sym].pop(0)
                    else:
                        lots[sym][0][0] -= consumed

                    sell_qty -= consumed

        for sym, sym_lots in lots.items():
            if not sym_lots:
                continue

            open_qty = sum(l[0] for l in sym_lots)
            if open_qty <= 0:
                continue

            avg_cost = (sum(l[0] * l[1] for l in sym_lots) / open_qty).quantize(
                Decimal("0.0001")
            )

            self._holdings[sym] = Holding(
                symbol=sym,
                company=meta[sym]["company"],
                sector=meta[sym]["sector"],
                quantity=open_qty,
                avg_cost=avg_cost,
                total_invested=total_invested[sym].quantize(Decimal("0.01")),
                total_fees=total_fees[sym].quantize(Decimal("0.01")),
                realised_pnl=realised_pnl[sym].quantize(Decimal("0.01")),
            )

    # ------------------------------------------------------------------ #
    #  Internal: enrich with live market data (sync)                      #
    # ------------------------------------------------------------------ #

    def _enrich(self, psx: "PSXScraperService") -> None:
        symbols = list(self._holdings.keys())

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
