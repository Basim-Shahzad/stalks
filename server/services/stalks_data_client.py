"""
Async HTTP client for the external Stalks Data API — the production stock
market data service (OHLCV bars, watchlist), authenticated via X-API-Key.
This is NOT this app's own database; see features/market/service.py for the
business logic that consumes it.
"""

from typing import Any

import httpx

from core.config import settings


class StalksDataAPIError(RuntimeError):
    """Raised when the external Stalks Data API returns an error response."""


class StalksDataClient:
    # One pooled client for the whole process (keep-alive / TLS reuse);
    # closed by close_shared_client() on shutdown.
    _shared_client: httpx.AsyncClient | None = None

    def __init__(self) -> None:
        self._base_url = settings.stalks_data_api_base_url.rstrip("/")
        self._headers = {"X-API-Key": settings.stalks_data_api_key.get_secret_value()}

    def _client(self) -> httpx.AsyncClient:
        cls = type(self)
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._headers,
                timeout=20,
                follow_redirects=True,
            )
        return cls._shared_client

    @classmethod
    async def close_shared_client(cls) -> None:
        if cls._shared_client is not None and not cls._shared_client.is_closed:
            await cls._shared_client.aclose()
        cls._shared_client = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = await self._client().request(method, path, **kwargs)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise StalksDataAPIError(
                f"Stalks Data API request failed: {method} {exc.request.url} "
                f"-> {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise StalksDataAPIError(
                f"Stalks Data API request failed: {method} {path}: {exc}"
            ) from exc
        return resp

    async def list_stock_prices(
        self,
        symbol: str,
        exchange: str,
        limit: int = 1000,
        sort: str = "asc",
    ) -> list[dict]:
        """Fetch daily OHLCV bars for a single symbol/exchange, unpaginated."""
        params = {
            "symbol": [symbol],
            "exchange": [exchange],
            "sort": sort,
            "paginate": False,
            "limit": limit,
        }
        resp = await self._request("GET", "/api/v1/stock-prices", params=params)
        data = resp.json()
        return data if isinstance(data, list) else data.get("items", [])
