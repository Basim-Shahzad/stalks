import unittest
from decimal import Decimal, InvalidOperation

from features.transactions.parsers.akd import (
    ParseResult,
    _DocState,
    _parse_decimal,
    _process_line,
)


class AkdParserTests(unittest.TestCase):
    def test_rejects_misgrouped_thousands_separator(self):
        with self.assertRaises(InvalidOperation):
            _parse_decimal("1,2")

        self.assertEqual(_parse_decimal("1,234.50"), Decimal("1234.50"))

    def test_preserves_fractional_quantity(self):
        state = _DocState()
        state.trade_date = "2026-10-29"
        state.current_side = "BUY"
        result = ParseResult()

        _process_line(
            "ABC Ready 1.5 10 0 0 0 0 0 0 0 0 15",
            0,
            state,
            result,
        )

        self.assertFalse(result.errors)
        self.assertEqual(result.transactions[0].quantity, Decimal("1.5"))
        self.assertEqual(result.transactions[0].to_dict()["quantity"], 1.5)


if __name__ == "__main__":
    unittest.main()
