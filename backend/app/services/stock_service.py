import yfinance as yf
from concurrent.futures import ThreadPoolExecutor


def fetch_single_ticker_basic(symbol):
    """Internal helper to fetch data for one ticker"""
    try:
        t = yf.Ticker(symbol)
        # Try fast_info first, fallback to history if needed
        price = t.fast_info.get("lastPrice")

        if price is None or price == 0:
            hist = t.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]
            else:
                return symbol, None

        # We only call .info for the Name if price was found (saves time)
        name = t.info.get("longName", "N/A")
        return symbol, {"name": name, "symbol": symbol, "price": round(float(price), 2)}
    except:
        return symbol, None


def get_bulk_stock_data(tickers, page=1, per_page=10):
    start = (page - 1) * per_page
    end = start + per_page
    paginated_tickers = tickers[start:end]

    results, working, broken = {}, [], []

    # Use ThreadPoolExecutor to fetch 10 tickers in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {
            executor.submit(fetch_single_ticker_basic, s): s for s in paginated_tickers
        }

        for future in future_to_ticker:
            symbol = future_to_ticker[future]
            try:
                sym, data = future.result()
                if data:
                    results[symbol] = data
                    working.append(symbol)
                else:
                    broken.append(symbol)
            except:
                broken.append(symbol)

    return {
        "prices": results,
        "working": working,
        "broken": broken,
        "total_count": len(tickers),
        "page": page,
        "per_page": per_page,
    }


def get_single_stock_detail(symbol):
    ticker_sym = symbol.upper()
    if "." not in ticker_sym
        ticker_sym += ".KA"

    try:
        t = yf.Ticker(ticker_sym)
        print(t.dividends)
        # 5d ensures we skip holidays/weekends and get at least 2 days
        hist = t.history(period="5d")

        if len(hist) < 2:
            return {"error": "Insufficient historical data available"}

        # Get last two rows (yesterday and today)
        prev_row = hist.iloc[-2]
        today_data = hist.iloc[-1]

        prev_close = float(prev_row["Close"])
        current_price = float(today_data["Close"])

        change_val = current_price - prev_close
        change_pct = (change_val / prev_close) * 100

        return {
            "symbol": ticker_sym,
            "current_price": round(current_price, 2),
            "previous_close": round(prev_close, 2),
            "today_high": round(float(today_data["High"]), 2),
            "today_low": round(float(today_data["Low"]), 2),
            "today_open": round(float(today_data["Open"]), 2),
            "change_amount": round(change_val, 2),
            "change_percent": round(change_pct, 2),
            "volume": int(today_data["Volume"]),
            "date": hist.index[-1].strftime("%Y-%m-%d"),
        }
    except Exception as e:
        return {"error": str(e)}
