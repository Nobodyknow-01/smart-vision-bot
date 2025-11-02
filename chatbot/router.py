# chatbot/router.py
"""
Universal router orchestrating intent detection and module calls.
Returns: (source_tag, reply_string)
source_tag in {"system","api","gnews","fact","ai","finance","weather","news"}
"""

import re
import traceback
from . import weather as weather_mod
from . import news as news_mod
from . import facts as facts_mod
from . import llm_client as llm
from . import ticker_map as ticker_map

def _is_weather(q):
    return bool(re.search(r"\b(weather|forecast|temperature|rain|rainfall|sunrise|sunset|wind|humidity)\b", q, re.I))

def _is_news(q):
    return bool(re.search(r"\b(news|headlines|breaking|latest)\b", q, re.I))

def _is_finance(q):
    return bool(re.search(r"\b(stock|share|price|bitcoin|crypto|btc|eth|market|nifty|sensex)\b", q, re.I))

def _is_fact(q):
    return bool(re.search(r"\b(who|what|when|where|tell me about|define|explain|is it true)\b", q, re.I))

def route(query: str, chat_history: list = None):
    """
    Main router function. Returns (source, reply)
    Priority:
      - Weather queries -> weather_mod.get_weather (API)
      - News queries -> news_mod.get_news (GNews -> fallback)
      - Finance -> ticker_map -> get_price_for_ticker
      - Facts -> facts_mod query (DuckDuckGo/Wiki wrappers)
      - Else -> llm_client.query_groq (LLM fallback)
    """
    q = (query or "").strip()
    try:
        # 1. Weather
        if _is_weather(q):
            try:
                text = weather_mod.get_weather(q)
                return ("weather", text)
            except Exception as e:
                return ("system", f"Weather module error: {e}")

        # 2. News
        if _is_news(q):
            try:
                items = news_mod.get_news(q)
                if isinstance(items, list):
                    return ("gnews", "\n\n".join(items))
                return ("gnews", str(items))
            except Exception as e:
                return ("system", f"News module error: {e}")

        # 3. Finance
        if _is_finance(q):
            try:
                ticker = ticker_map.extract_ticker(q)
                if ticker:
                    price = ticker_map.get_price_for_ticker(ticker)
                    return ("finance", price)
                else:
                    return ("finance", "Please specify a company or ticker (e.g., 'Tata Motors', 'AAPL', 'BTC').")
            except Exception as e:
                return ("system", f"Finance module error: {e}")

        # 4. Facts / current-info
        if _is_fact(q) or any(k in q.lower() for k in ("current", "latest", "today", "now", "as of")):
            # facts_mod should implement search using DuckDuckGo & Wikipedia (improve if needed)
            try:
                fact = facts_mod.query_facts(q)
                if fact:
                    return ("fact", fact)
            except Exception as e:
                # continue to other fallbacks
                pass

        # 5. Fallback to LLM but prefer real-time helpers for 'current' keywords
        try:
            ai_resp = llm.query_groq(q)
            if ai_resp:
                return ("ai", ai_resp)
        except Exception as e:
            pass

        return ("system", "Sorry — I couldn't answer that right now.")
    except Exception as e:
        traceback.print_exc()
        return ("system", f"Router error: {e}")
