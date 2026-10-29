import unittest
from datetime import date
from decimal import Decimal

from features.portfolios.holdings import OpenLot
from features.strategies.sell.bracket import BracketStrategy


class BracketStrategyTests(unittest.TestCase):
    def test_rounds_volume_once_across_same_symbol_lots(self):
        strategy = object.__new__(BracketStrategy)
        strategy._triggered = [
            (
                OpenLot("ABC", Decimal("1"), Decimal("10"), Decimal("10"), date.today()),
                {"current": Decimal("12")},
            )
            for _ in range(3)
        ]
        strategy.sell_volume_pct = 0.5
        strategy.account_id = 1
        strategy.upper_sell_bracket_pct = 1.05

        orders = strategy.format_limit_orders()

        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["Volume"], 2)

    def test_never_rounds_above_fractional_total_position(self):
        strategy = object.__new__(BracketStrategy)
        strategy._triggered = [
            (
                OpenLot("ABC", Decimal("0.75"), Decimal("10"), Decimal("10"), date.today()),
                {"current": Decimal("12")},
            ),
            (
                OpenLot("ABC", Decimal("0.75"), Decimal("10"), Decimal("10"), date.today()),
                {"current": Decimal("12")},
            ),
        ]
        strategy.sell_volume_pct = 1.0
        strategy.account_id = 1
        strategy.upper_sell_bracket_pct = 1.05

        orders = strategy.format_limit_orders()

        self.assertEqual(orders[0]["Volume"], 1)


if __name__ == "__main__":
    unittest.main()
