# finance.py
"""
Enhanced finance module for Smart Vision Bot.

Supports:
- Global stock quotes (via yfinance)
- Cryptocurrencies (BTC, ETH, etc.)
- Indices & commodities (Dow Jones, Nifty 50, Gold, Oil)
- Country-level macroeconomic data (GDP, inflation) via World Bank API
"""

import yfinance as yf
import requests
import re

# -----------------------
# Stock / Crypto Prices
# -----------------------
def get_price(symbol: str) -> str:
    """
    Get the latest price for a stock, index, commodity, or crypto.
    Examples:
      - "AAPL" (Apple Inc.)
      - "TCS.NS" (TCS in India NSE)
      - "BTC-USD" (Bitcoin)
      - "^NSEI" (Nifty 50 Index)
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Some tickers require fast_info for price
        price = info.get("regularMarketPrice") or getattr(ticker.fast_info, "last_price", None)
        currency = info.get("currency", "USD")

        if price:
            return f"{symbol.upper()} → {price} {currency}"

        return f"No price data found for {symbol}."
    except Exception as e:
        return f"Finance error fetching {symbol}: {e}"

# -----------------------
# Company / Symbol Search
# -----------------------
def search_symbol(query: str) -> str:
    """
    Try to guess the ticker for a company/crypto/index.
    Example: "Tesla stock" → TSLA
    """
    try:
        q = re.sub(r"(stock|share|price|quote)", "", query, flags=re.I).strip()
        tickers = yf.search(q)
        if tickers and "quotes" in tickers and tickers["quotes"]:
            first = tickers["quotes"][0]
            return first.get("symbol", "")
    except Exception:
        return ""
    return ""

# -----------------------
# Macroeconomics (World Bank API)
# -----------------------
def get_gdp(country: str) -> str:
    """Fetch GDP for a given country (latest year available)."""
    try:
        url = f"http://api.worldbank.org/v2/country/{country}/indicator/NY.GDP.MKTP.CD?format=json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1 and data[1]:
                latest = data[1][0]
                value = latest.get("value")
                year = latest.get("date")
                if value:
                    value_billion = round(value / 1e9, 2)
                    return f"{country.upper()} GDP in {year}: {value_billion} Billion USD"
        return f"GDP data not available for {country}."
    except Exception as e:
        return f"Error fetching GDP: {e}"

def get_inflation(country: str) -> str:
    """Fetch inflation rate for a given country (latest year)."""
    try:
        url = f"http://api.worldbank.org/v2/country/{country}/indicator/FP.CPI.TOTL.ZG?format=json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1 and data[1]:
                latest = data[1][0]
                value = latest.get("value")
                year = latest.get("date")
                if value:
                    return f"{country.upper()} inflation in {year}: {value:.2f}%"
        return f"Inflation data not available for {country}."
    except Exception as e:
        return f"Error fetching inflation: {e}"

# -----------------------
# Universal Finance Router
# -----------------------
def get_finance_info(query: str) -> str:
    """
    Universal entry point for finance queries.
    Decides whether to fetch stock/crypto price or macroeconomic data.
    """
    q = query.lower()

    # Check for GDP
    if "gdp" in q:
        # Expect query like "gdp of india"
        match = re.search(r"gdp of ([a-z\s]+)", q)
        if match:
            country = match.group(1).strip().lower()
            return get_gdp(country)
        return "Please specify a country for GDP."

    # Check for inflation
    if "inflation" in q:
        match = re.search(r"inflation of ([a-z\s]+)", q)
        if match:
            country = match.group(1).strip().lower()
            return get_inflation(country)
        return "Please specify a country for inflation."

    # Otherwise assume stock/crypto
    # Try direct ticker first
    words = q.replace("price", "").replace("stock", "").strip()
    symbol = search_symbol(words) or words.upper()
    return get_price(symbol)
