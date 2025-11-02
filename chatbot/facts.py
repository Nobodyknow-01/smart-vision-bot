# facts.py
"""
Enhanced facts module for Smart Vision Bot.

Features:
- Robust Wikipedia querying using MediaWiki REST & action APIs with informative User-Agent
- Graceful fallback to DuckDuckGo instant answer API
- Normalizes user queries (removes "who is", "what is", etc.)
- Retry/backoff for transient failures and clear debug logging
- Returns short, cleaned extracts suitable for chat display
"""

from typing import Optional, Tuple
import requests
import time
import re
import urllib.parse

# Optional fallback to the `wikipedia` package if available
try:
    import wikipedia as _wikipedia_pkg  # type: ignore
except Exception:
    _wikipedia_pkg = None

# Set a polite User-Agent to avoid 403 from Wikimedia
DEFAULT_HEADERS = {
    "User-Agent": "SmartVisionBot/1.0 (https://example.local/) Python/requests"
}

# Simple in-memory cache to reduce repeated API calls
_CACHE = {}

def _clean(text: str, max_len: int = 800) -> str:
    """Normalize whitespace and trim length."""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) > max_len:
        t = t[:max_len].rsplit(" ", 1)[0] + "..."
    return t

def _normalize_query(q: str) -> str:
    """Remove common leading question phrases that confuse the wiki search."""
    q = q.strip()
    q = re.sub(r"^(who is|who's|what is|what's|tell me about|give me info on|find info about|about)\s+", "", q, flags=re.I)
    q = q.replace("?", "").strip()
    return q

# ---------------------------
# DuckDuckGo Instant Answer
# ---------------------------
def query_duckduckgo(query: str, timeout: int = 8) -> str:
    """Query DuckDuckGo Instant Answer API for short factual answers."""
    key = ("ddg", query.lower())
    if key in _CACHE:
        return _CACHE[key]

    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    try:
        resp = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            # Prefer AbstractText if present
            if data.get("AbstractText"):
                txt = _clean(data["AbstractText"], max_len=1000)
                _CACHE[key] = txt
                return txt
            # Next, try Abstract or Definition
            if data.get("Definition"):
                txt = _clean(data["Definition"], max_len=1000)
                _CACHE[key] = txt
                return txt
            # Try RelatedTopics
            related = data.get("RelatedTopics", [])
            for item in related:
                if isinstance(item, dict):
                    t = item.get("Text") or item.get("Result")
                    if t:
                        txt = _clean(t, max_len=1000)
                        _CACHE[key] = txt
                        return txt
        else:
            # Rate-limited or other status
            # DuckDuckGo sometimes returns 202 for rate limiting; treat as no-answer
            return ""
    except Exception:
        return ""
    return ""

# ---------------------------
# Wikipedia (MediaWiki APIs)
# ---------------------------
def _wiki_summary(title: str, timeout: int = 8) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempt to fetch the REST summary for a given page title.
    Returns tuple (extract, url) or (None, None) on failure.
    """
    title_enc = urllib.parse.quote(title)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_enc}"
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if r.status_code == 200:
            j = r.json()
            extract = j.get("extract") or j.get("description") or ""
            page_url = j.get("content_urls", {}).get("desktop", {}).get("page") or f"https://en.wikipedia.org/wiki/{title_enc}"
            if extract:
                return _clean(extract, max_len=1200), page_url
            # If a disambiguation without extract, return empty to trigger search
            return "", page_url
        # 404 or other: return None for caller to search
        return None, None
    except Exception:
        return None, None

def _wiki_search(query: str, timeout: int = 8) -> Optional[str]:
    """
    Use the MediaWiki 'search' (action=query&list=search) to find the best title.
    Returns the best-matching page title or None.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 5,
        "srprop": ""
    }
    try:
        r = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            hits = data.get("query", {}).get("search", [])
            if hits:
                # Prefer exact match by title if available
                for h in hits:
                    title = h.get("title", "")
                    if title.lower() == query.lower():
                        return title
                # Otherwise return the top hit
                return hits[0].get("title")
    except Exception:
        return None
    return None

def query_wikipedia(query: str) -> str:
    """
    Robust Wikipedia query:
    1) Normalize query
    2) Try direct REST summary for the phrase
    3) If not found → run search, then summary on top result
    4) If REST fails (403/others) try the 'opensearch' endpoint as a fallback
    """
    key = ("wiki", query.lower())
    if key in _CACHE:
        return _CACHE[key]

    q = _normalize_query(query)
    # Try direct summary first (good for explicit titles like "Barack Obama")
    extract, page_url = _wiki_summary(q)
    if extract:
        out = f"{extract} — {page_url}"
        _CACHE[key] = out
        return out

    # If REST returned (None,None) or empty extract try a search
    title = _wiki_search(q)
    if title:
        # ask summary for found title
        extract2, page_url2 = _wiki_summary(title)
        if extract2:
            out = f"{extract2} — {page_url2}"
            _CACHE[key] = out
            return out

    # opensearch fallback (less structured but sometimes works)
    try:
        opensearch_url = "https://en.wikipedia.org/w/api.php"
        params = {"action": "opensearch", "search": q, "limit": 3, "namespace": 0, "format": "json"}
        r = requests.get(opensearch_url, params=params, headers=DEFAULT_HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            if len(data) >= 2 and data[1]:
                # pick first suggestion
                title = data[1][0]
                extract3, page_url3 = _wiki_summary(title)
                if extract3:
                    out = f"{extract3} — {page_url3}"
                    _CACHE[key] = out
                    return out
    except Exception:
        pass

    # As a last resort, try the wikipedia python package if available
    if _wikipedia_pkg:
        try:
            # set safe language and user agent
            _wikipedia_pkg.set_lang("en")
            txt = _wikipedia_pkg.summary(q, sentences=3, auto_suggest=True, redirect=True)
            txt = _clean(txt, max_len=1200)
            _CACHE[key] = txt
            return txt
        except Exception:
            pass

    # Nothing found
    return ""

def get_fact(query: str) -> str:
    """
    Public helper: try Wikipedia first, then DuckDuckGo.
    Returns a plain text answer or empty string if nothing found.
    """
    # Try wikipedia first
    wiki_answer = query_wikipedia(query)
    if wiki_answer:
        return wiki_answer + " (Wikipedia)"

    ddg_answer = query_duckduckgo(query)
    if ddg_answer:
        return ddg_answer + " (DuckDuckGo)"

    return "I couldn't find a concise factual answer for that."
