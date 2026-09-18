from services.stalks_data_client import StalksDataClient

from .schemas.MarketSchema import MarketDataResponse, OHLCVBar


class MarketService:
    def __init__(self, client: StalksDataClient):
        self.client = client

    async def get_ohlcv(self, exchange: str, symbol: str, limit: int = 365) -> MarketDataResponse:
        exchange = exchange.upper()
        symbol = symbol.upper()

        rows = await self.client.list_stock_prices(
            symbol=symbol, exchange=exchange, limit=limit, sort="asc"
        )

        bars = [
            OHLCVBar(
                date=row["timestamp"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
            for row in rows
        ]

        return MarketDataResponse(exchange=exchange, symbol=symbol, rows=len(bars), data=bars)
