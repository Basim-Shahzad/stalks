import io
import csv
from decimal import Decimal, ROUND_HALF_UP
from functools import cached_property
from dependencies.strategies.Strategy import Strategy
from models.Transaction import Transaction


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
        trigger_pct: float = 1.3,
        account_id: int = 110310,
        upper_sell_bracket_pct: float = 1.02,  # means 2%
        stop_price_pct: float = 0.95,  # means -5%
        sell_volume_pct: float = 0.25,  # means 25%
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

    def filter_triggered_stocks(self) -> tuple[list[Transaction], list[dict]]:
        triggered_tsxs: list[Transaction] = []
        triggered_stocks: list[dict] = []

        for tsx in self.transactions:
            for stock in self.current_stocks_data:
                if stock["symbol"] == tsx.symbol:
                    if stock["current"] >= (tsx.rate * Decimal(str(self.trigger_pct))):
                        triggered_tsxs.append(tsx)
                        triggered_stocks.append(stock)

        return triggered_tsxs, triggered_stocks

    def format_transactions(self) -> list[dict]:
        orders = []
        triggered_tsxs, triggered_stocks = self.filter_triggered_stocks()

        for tsx, stock in zip(triggered_tsxs, triggered_stocks):
            current_price = stock["current"]
            upper_price = round(
                current_price * Decimal(str(self.upper_sell_bracket_pct)), 2
            )
            stop_price = round(current_price * Decimal(str(self.stop_price_pct)), 2)
            sell_volume = int(
                (tsx.quantity * Decimal(str(self.sell_volume_pct))).to_integral_value(
                    rounding=ROUND_HALF_UP
                )
            )

            if sell_volume < 1:
                continue

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

    def to_csv_basket(self):

        orders = self.format_transactions()
        output = io.StringIO()

        writer = csv.DictWriter(output, fieldnames=self.HEADERS)
        writer.writeheader()

        for order in orders:
            row = {header: order.get(header, "") for header in self.HEADERS}
            writer.writerow(row)

        return output.getvalue()
