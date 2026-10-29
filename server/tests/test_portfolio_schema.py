import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from features.portfolios.schemas.PortfolioSchema import (
    PortfolioCreateSchema,
    PortfolioSchema,
)
from models.enums import ExchangeType


class PortfolioSchemaTests(unittest.TestCase):
    def test_create_schema_does_not_accept_client_currency(self):
        portfolio = PortfolioCreateSchema(
            exchange=ExchangeType.US,
            name="US holdings",
            currency="PKR",
        )

        self.assertNotIn("currency", portfolio.model_dump())
        self.assertEqual(portfolio.exchange, ExchangeType.US)
        self.assertIsNone(portfolio.description)

    def test_null_description_is_valid_in_portfolio_response(self):
        portfolio = SimpleNamespace(
            id=UUID("ab71e11a-5391-4f4d-8a25-1aafc1473af1"),
            exchange=ExchangeType.US,
            currency="USD",
            name="US holdings",
            description=None,
            broker=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        response = PortfolioSchema.model_validate(portfolio)

        self.assertIsNone(response.description)
        self.assertEqual(response.currency, "USD")


if __name__ == "__main__":
    unittest.main()
