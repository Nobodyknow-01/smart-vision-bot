# llm_client.py
"""
Enhanced LLM client for Smart Vision Bot
- Groq for reasoning / fallback
- Real-time trigger for queries with "latest", "current", "today", "now", "2025"
- DuckDuckGo + Wikipedia fallback for freshness
"""

import os
import requests
import re

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.1-8b-instant"   # ✅ supported model
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# -----------------------
# Helpers
# -----------------------
def is_real_time_query(prompt: str) -> bool:
    keywords = ["latest", "current", "today", "now", "2025", "as of"]
    return any(k in prompt.lower() for k in keywords)

def fetch_duckduckgo(query: str) -> str:
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("AbstractText"):
                return data["AbstractText"]
            if "RelatedTopics" in data and data["RelatedTopics"]:
                return data["RelatedTopics"][0].get("Text", "")
    except Exception:
        return ""
    return ""

def fetch_wikipedia(query: str) -> str:
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        r = requests.get(url, timeout=10, headers={"User-Agent": "SmartVisionBot/1.0"})
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", "")
    except Exception:
        return ""
    return ""

# -----------------------
# Main Query
# -----------------------
def query_groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        return "Groq API key not found."

    # 🚨 Real-time trigger: skip outdated AI
    if is_real_time_query(prompt):
        # Try DuckDuckGo first
        ans = fetch_duckduckgo(prompt)
        if ans:
            return ans + " (DuckDuckGo, real-time)"
        # Try Wikipedia
        ans = fetch_wikipedia(prompt)
        if ans:
            return ans + " (Wikipedia, latest)"
        # If fails, fallback to LLM
        return _query_groq_llm(prompt)

    # Default → LLM
    return _query_groq_llm(prompt)

def _query_groq_llm(prompt: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a concise factual assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 512,
        }
        r = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print("Groq API error:", r.status_code, r.text)
            return ""
    except Exception as e:
        print("Groq API exception:", e)
        return ""
