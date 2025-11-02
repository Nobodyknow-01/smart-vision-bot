# news.py
"""
Enhanced News module for Smart Vision Bot
- Smarter query cleaning
- Retry with variations if no articles found
- Proper error handling & logging
- Multi-source fallback (GNews → Bing → DuckDuckGo)
"""

import os
import requests
import re


from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

def clean_query(query: str) -> str:
    """Extract main topic from query (remove 'news' keywords)."""
    q = query.lower().strip()
    q = re.sub(r"\b(news|headline|headlines)\b", "", q)  # remove 'news' anywhere
    return q.strip() or "world"

def fetch_gnews(q: str) -> list:
    """Fetch from GNews API."""
    if not GNEWS_API_KEY:
        return []
    try:
        url = f"https://gnews.io/api/v4/search?q={q}&token={GNEWS_API_KEY}&lang=en&max=5&sortby=publishedAt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("articles"):
                return [
                    f"📰 {a['title']} - {a['source']['name']}\n   {a.get('description','')}"
                    for a in data["articles"][:5]
                ]
            else:
                # Retry with 'AND' for better match
                if " " in q:
                    q_alt = " AND ".join(q.split())
                    return fetch_gnews(q_alt)
        elif r.status_code == 401:
            return ["❌ Invalid GNews API key."]
        elif r.status_code == 429:
            return ["⚠️ GNews quota exceeded for today."]
    except Exception as e:
        return [f"News fetch failed (GNews): {e}"]
    return []

def fetch_bing(q: str) -> list:
    """Fallback: Bing News API."""
    BING_KEY = os.getenv("BING_API_KEY")
    if not BING_KEY:
        return []
    try:
        url = f"https://api.bing.microsoft.com/v7.0/news/search?q={q}&mkt=en-US&count=5"
        headers = {"Ocp-Apim-Subscription-Key": BING_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "value" in data:
                return [
                    f"📰 {a['name']} - {a['provider'][0]['name']}\n   {a.get('description','')}"
                    for a in data["value"][:5]
                ]
    except Exception:
        pass
    return []

def fetch_duckduckgo(q: str) -> list:
    """Fallback: DuckDuckGo (lite)."""
    try:
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "RelatedTopics" in data and data["RelatedTopics"]:
                return [f"📰 {t.get('Text')}" for t in data["RelatedTopics"][:5]]
    except Exception:
        pass
    return []

def get_news(query: str = "world") -> list:
    """Unified news fetcher with fallbacks."""
    q = clean_query(query)

    # Primary → GNews
    news = fetch_gnews(q)
    if news: return news

    # Secondary → Bing
    news = fetch_bing(q)
    if news: return news

    # Fallback → DuckDuckGo
    news = fetch_duckduckgo(q)
    if news: return news

    return [f"No news found for '{q}'. Try rephrasing."]
