import io
import csv
from decimal import Decimal, ROUND_HALF_UP
from functools import cached_property
from features.portfolios.holdings import OpenLot
from features.transactions.models.Transaction import Transaction

from ..strategy import Strategy


class BracketStrategy(Strategy):
    HEADERS = [
        "Account",
        "Symbol",
        "Order Side",
        "Volume",
        "Price",
        "Order Type",
        "Limit Price",
    ]

    def __init__(
        self,
        symbols: list[str],
        transactions: list[Transaction],
        trigger_pct: float,
        account_id: int,
        upper_sell_bracket_pct: float,
        stop_price_pct: float,
        sell_volume_pct: float,
    ):
        super().__init__(symbols, transactions)
        self.trigger_pct = trigger_pct
        self.account_id = account_id
        self.upper_sell_bracket_pct = upper_sell_bracket_pct
        self.stop_price_pct = stop_price_pct
        self.sell_volume_pct = sell_volume_pct

    @cached_property
    def current_stocks_data(self) -> list[dict]:
        return self.get_psx_data()

    @cached_property
    def _triggered(self) -> list[tuple[OpenLot, dict]]:
        """Open lots whose live price has reached `rate * trigger_pct`."""
        stocks = {
            stock["symbol"]: stock
            for stock in self.current_stocks_data
            if stock.get("current") is not None
        }
        multiplier = Decimal(str(self.trigger_pct))

        triggered: list[tuple[OpenLot, dict]] = []
        for lot in self.get_open_lots():
            stock = stocks.get(lot.symbol)
            if stock is not None and stock["current"] >= lot.rate * multiplier:
                triggered.append((lot, stock))
        return triggered

    def _triggered_by_symbol(self) -> list[tuple[str, dict, Decimal]]:
        grouped: dict[str, tuple[dict, Decimal]] = {}
        for lot, stock in self._triggered:
            current = grouped.get(lot.symbol)
            quantity = lot.quantity + (current[1] if current else Decimal("0"))
            grouped[lot.symbol] = (stock, quantity)

        return [
            (symbol, stock, quantity)
            for symbol, (stock, quantity) in grouped.items()
        ]

    def _sell_volume(self, quantity: Decimal) -> int:
        rounded_volume = int(
            (quantity * Decimal(str(self.sell_volume_pct))).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )
        return min(rounded_volume, int(quantity))

    def format_limit_orders(self) -> list[dict]:
        orders = []
        for symbol, stock, quantity in self._triggered_by_symbol():
            sell_volume = self._sell_volume(quantity)
            if sell_volume < 1:
                continue

            upper_price = round(
                stock["current"] * Decimal(str(self.upper_sell_bracket_pct)), 2
            )
            orders.append(
                {
                    "Account": self.account_id,
                    "Symbol": symbol,
                    "Order Side": "SELL",
                    "Volume": sell_volume,
                    "Price": upper_price,
                    "Order Type": "LIMIT",
                    "Limit Price": upper_price,
                }
            )

        return orders

    def format_slo_orders(self) -> list[dict]:
        orders = []
        for symbol, stock, quantity in self._triggered_by_symbol():
            sell_volume = self._sell_volume(quantity)
            if sell_volume < 1:
                continue

            stop_price = round(stock["current"] * Decimal(str(self.stop_price_pct)), 2)
            orders.append(
                {
                    "Account": self.account_id,
                    "Symbol": symbol,
                    "Order Side": "SELL",
                    "Volume": sell_volume,
                    "Price": stop_price,
                    "Order Type": "SLO",
                    "Limit Price": stop_price,
                }
            )

        return orders

    def _to_csv(self, orders: list[dict]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.HEADERS)
        writer.writeheader()
        for order in orders:
            writer.writerow({header: order.get(header, "") for header in self.HEADERS})
        return output.getvalue()

    def to_limit_csv_basket(self) -> str:
        return self._to_csv(self.format_limit_orders())

    def to_slo_csv_basket(self) -> str:
        return self._to_csv(self.format_slo_orders())
