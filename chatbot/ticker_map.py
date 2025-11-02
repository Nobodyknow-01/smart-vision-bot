import re

COMMON_MAP = {
    "tata motors": "TATAMOTORS.NS", "reliance": "RELIANCE.NS", "infosys": "INFY.NS",
    "itc": "ITC.NS", "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS",
    "sbi": "SBIN.NS", "adani": "ADANIENT.NS", "mrf": "MRF.NS", "tvs": "TVSMOTOR.NS",
    "apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT", "amazon": "AMZN", "tesla": "TSLA", "meta": "META",
    "nifty": "^NSEI", "sensex": "^BSESN", "nasdaq": "^IXIC", "dow jones": "^DJI", "s&p 500": "^GSPC",
    "bitcoin": "BTC-USD", "btc": "BTC-USD", "ethereum": "ETH-USD", "eth": "ETH-USD", "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
}

CRYPTO_KEYWORDS = {"bitcoin": "BTC-USD", "btc": "BTC-USD", "ethereum": "ETH-USD", "eth": "ETH-USD", "dogecoin": "DOGE-USD", "doge": "DOGE-USD"}

def extract_ticker(query: str):
    q = (query or "").lower()

    # 1. Crypto detection first
    for k, v in CRYPTO_KEYWORDS.items():
        if k in q:
            return v

    # 2. Common map
    for k, v in COMMON_MAP.items():
        if k in q:
            return v

    # 3. Regex for ticker symbols
    m = re.search(r"\b([A-Z]{1,6})(?:\.[A-Z]{1,3})?\b", query.upper())
    if m: return m.group(0)

    # 4. Yahoo Finance fallback
    try:
        import yfinance as yf
        result = yf.Ticker(query.upper())
        if hasattr(result, "info") and "symbol" in result.info:
            return result.info["symbol"]
    except Exception:
        pass

    return None

def get_price_for_ticker(ticker: str):
    try:
        import yfinance as yf
        # Stocks
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d")
            if not hist.empty:
                return f"{ticker}: {hist['Close'].iloc[-1]:.2f}"
        except Exception:
            pass

        # Cryptos
        if ticker and ticker.endswith("-USD"):
            try:
                from pycoingecko import CoinGeckoAPI
                cg = CoinGeckoAPI()
                id_map = {"BTC-USD": "bitcoin", "ETH-USD": "ethereum", "DOGE-USD": "dogecoin"}
                coin = id_map.get(ticker, ticker.lower())
                res = cg.get_price(ids=coin, vs_currencies=["usd", "inr"])
                if res and coin in res:
                    return f"{coin.capitalize()}: ${res[coin]['usd']:.2f} / ₹{res[coin]['inr']:.2f}"
            except Exception:
                pass

        return f"❌ Price not found for {ticker}."
    except Exception as e:
        return f"⚠️ Finance error: {e}"
