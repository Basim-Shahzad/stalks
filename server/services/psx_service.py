import requests
from decimal import Decimal
from bs4 import BeautifulSoup


class PSXScraperService:
    """
    Service class for scraping PSX market watch data.
    """

    URL = "https://dps.psx.com.pk/market-watch"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://dps.psx.com.pk/",
        "Connection": "keep-alive",
    }

    def __init__(self):
        # Use a session for connection pooling (faster subsequent requests)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _fetch_html(self, timeout: int = 20) -> str:
        """Fetches the raw HTML from the PSX website."""
        resp = self.session.get(self.URL, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    def _parse_html(self, html: str) -> list[dict]:
        """Parses the HTML and extracts the market watch table into a list of dicts."""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="tbl")

        if table is None:
            raise ValueError("Could not find the market-watch table in the HTML.")

        results = []

        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) < 11:
                continue

            sym_cell = cells[0]
            sym_link = sym_cell.find("a", class_="tbl__symbol")
            symbol = sym_cell.get("data-search", "").strip()
            company = (
                sym_link["data-title"].strip()
                if sym_link and sym_link.get("data-title")
                else ""
            )

            tag_div = sym_cell.find("div", class_="tag")
            tag = tag_div.get_text(strip=True) if tag_div else ""

            sector = cells[1].get_text(strip=True)
            indices = cells[2].get_text(strip=True)

            def num(cell):
                raw = cell.get("data-order", "").strip()
                try:
                    return Decimal(raw) if raw else None
                except ValueError:
                    return None

            change_cell = cells[8]
            classes = change_cell.get("class", [])
            if "change__text--pos" in classes:
                direction = "up"
            elif "change__text--neg" in classes:
                direction = "down"
            else:
                direction = "flat"

            results.append(
                {
                    "symbol": symbol,
                    "company": company,
                    "tag": tag,
                    "sector": sector,
                    "indices": indices,
                    "ldcp": num(cells[3]),
                    "open": num(cells[4]),
                    "high": num(cells[5]),
                    "low": num(cells[6]),
                    "current": num(cells[7]),
                    "change": num(cells[8]),
                    "change_pct": num(cells[9]),
                    "volume": num(cells[10]),
                    "direction": direction,
                }
            )

        return results

    def get_market_data(self, symbols: list[str] | None = None) -> list[dict]:
        """
        Public method to get market data.
        Optionally filter by a list of symbols (e.g., ["HBL", "OGDC"]).
        """
        html = self._fetch_html()
        records = self._parse_html(html)

        if symbols:
            lookup = {s.upper() for s in symbols}
            records = [r for r in records if r["symbol"].upper() in lookup]

        return records
