from services.psx_service import PSXScraperService
from features.transactions.models.Transaction import Transaction

psx = PSXScraperService()

class Strategy:

    def __init__(self, symbols: list[str], transactions: list[Transaction]):
        self.symbols = symbols
        self.transactions = transactions

    def get_psx_data(self):
        return psx.get_market_data(self.symbols)

    def get_yf_data(self):
        pass