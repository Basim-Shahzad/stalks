from features.portfolios.holdings import Holdings, OpenLot
from features.transactions.models.Transaction import Transaction
from services.psx_service import psx_service


class Strategy:

    def __init__(self, symbols: list[str], transactions: list[Transaction]):
        self.symbols = symbols
        self.transactions = transactions

    def get_psx_data(self) -> list[dict]:
        """Live quotes for `symbols`. Blocking (cached network call): run the
        strategy via asyncio.to_thread from async code."""
        return psx_service.get_market_data(self.symbols)

    def get_open_lots(self) -> list[OpenLot]:
        """Purchase lots still held after FIFO-matching every sell, so a
        strategy never acts on shares that were already sold."""
        return Holdings.from_transactions(self.transactions).open_lots

    def get_yf_data(self):
        pass
