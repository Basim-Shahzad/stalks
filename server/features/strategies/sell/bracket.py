import io
import csv
from decimal import Decimal, ROUND_HALF_UP
from functools import cached_property
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
    def _triggered(self) -> tuple[list[Transaction], list[dict]]:
        triggered_tsxs: list[Transaction] = []
        triggered_stocks: list[dict] = []

        for tsx in self.transactions:
            for stock in self.current_stocks_data:
                if stock["symbol"] == tsx.symbol:
                    if stock["current"] >= (tsx.rate * Decimal(str(self.trigger_pct))):
                        triggered_tsxs.append(tsx)
                        triggered_stocks.append(stock)

        return triggered_tsxs, triggered_stocks

    def _compute_sell_volume(self, tsx: Transaction) -> int:
        return int(
            (tsx.quantity * Decimal(str(self.sell_volume_pct))).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )

    def format_limit_orders(self) -> list[dict]:
        orders = []
        triggered_tsxs, triggered_stocks = self._triggered

        for tsx, stock in zip(triggered_tsxs, triggered_stocks):
            sell_volume = self._compute_sell_volume(tsx)
            if sell_volume < 1:
                continue

            upper_price = round(
                stock["current"] * Decimal(str(self.upper_sell_bracket_pct)), 2
            )
            orders.append(
                {
                    "Account": self.account_id,
                    "Symbol": tsx.symbol,
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
        triggered_tsxs, triggered_stocks = self._triggered

        for tsx, stock in zip(triggered_tsxs, triggered_stocks):
            sell_volume = self._compute_sell_volume(tsx)
            if sell_volume < 1:
                continue

            stop_price = round(stock["current"] * Decimal(str(self.stop_price_pct)), 2)
            orders.append(
                {
                    "Account": self.account_id,
                    "Symbol": tsx.symbol,
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
