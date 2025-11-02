# chatbot/weather.py
"""
Enhanced weather module using Open-Meteo (global), with proper geocoding and detailed forecast support.
Fixed issue: detailed weather queries were defaulting to Pune.
"""

import requests
import re
from datetime import datetime, timedelta
from dateutil import parser as dateparser

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
IPAPI_URL = "https://ipapi.co/json/"

def _geocode_place(place: str):
    """Return (name, lat, lon) for a given place."""
    if not place:
        return None
    try:
        params = {"name": place, "count": 1, "language": "en", "format": "json"}
        r = requests.get(GEOCODING_URL, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            res = data["results"][0]
            return (res.get("name") or place, float(res["latitude"]), float(res["longitude"]))
    except Exception:
        return None
    return None

def _ip_location():
    """Fallback to approximate location from IP address."""
    try:
        r = requests.get(IPAPI_URL, timeout=4).json()
        return (r.get("city") or "your location", float(r["latitude"]), float(r["longitude"]))
    except Exception:
        return None

def _format_temp(t):
    return f"{t:.1f}°C" if t is not None else "N/A"

def _format_val(v):
    try:
        return f"{v:.1f}"
    except Exception:
        return "N/A"

def _extract_city(query: str) -> str:
    """Robustly extract the city name from any weather-related query."""
    q = query.strip()
    # Remove common filler words but keep context
    q = re.sub(r"\b(weather|forecast|report|today|tomorrow|yesterday|detailed|detail|full|show|give|about|in|of|at|for|the)\b", "", q, flags=re.I)
    q = re.sub(r"[^A-Za-z\s\-]", "", q)
    city = q.strip().title()
    return city if city else None

def get_weather(query: str) -> str:
    """
    Handles queries like:
      - "weather of Mumbai"
      - "weather in London tomorrow"
      - "today weather New York"
      - "weather of Tokyo 2025-09-01"
      - "detailed weather Mumbai"
    """
    try:
        q = (query or "").strip()
        date = None
        detail = False

        # check if user asked for detailed report
        if re.search(r"\b(detail|detailed|report|full|forecast)\b", q, re.I):
            detail = True

        # handle dates: yesterday, today, tomorrow, explicit date
        if re.search(r"\byesterday\b", q, re.I):
            date = (datetime.utcnow() - timedelta(days=1)).date()
        elif re.search(r"\btomorrow\b", q, re.I):
            date = (datetime.utcnow() + timedelta(days=1)).date()
        elif re.search(r"\btoday\b", q, re.I):
            date = datetime.utcnow().date()
        else:
            m = re.search(r"(\b\d{4}-\d{2}-\d{2}\b)|on\s+([A-Za-z0-9,\s\-]+)", q, re.I)
            if m:
                try:
                    candidate = (m.group(1) or m.group(2)).strip()
                    parsed = dateparser.parse(candidate, fuzzy=True)
                    if parsed:
                        date = parsed.date()
                except Exception:
                    pass

        # extract city name
        city = _extract_city(q)
        geo = _geocode_place(city) if city else None
        if not geo:
            geo = _ip_location()
            if not geo:
                return "❌ Couldn't determine location. Please specify a city (e.g., 'weather in Mumbai')."

        name, lat, lon = geo

        # -------- If user asked for specific date --------
        if date:
            params = {
                "latitude": lat,
                "longitude": lon,
                "timezone": "auto",
                "current_weather": "true",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset",
                "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,windgusts_10m,precipitation",
                "start_date": date.isoformat(),
                "end_date": date.isoformat(),
            }
            r = requests.get(OPEN_METEO_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()

            daily = data.get("daily", {})
            hourly = data.get("hourly", {})
            lines = [f"📅 Weather for {name} ({date.isoformat()}):"]

            if daily:
                tmax = daily.get("temperature_2m_max", [None])[0]
                tmin = daily.get("temperature_2m_min", [None])[0]
                prec = daily.get("precipitation_sum", [None])[0]
                sunrise = daily.get("sunrise", [None])[0]
                sunset = daily.get("sunset", [None])[0]
                lines.append(f"• Temp Range: {_format_val(tmin)}°C — {_format_val(tmax)}°C")
                lines.append(f"• Precipitation: {_format_val(prec)} mm")
                if sunrise and sunset:
                    lines.append(f"• Sunrise: {sunrise.split('T')[-1]}, Sunset: {sunset.split('T')[-1]}")

            if detail and hourly:
                lines.append("\n🕒 Hourly Snapshot (next 6h):")
                for tt, tp, hm, ws in zip(
                    hourly.get("time", [])[:6],
                    hourly.get("temperature_2m", [])[:6],
                    hourly.get("relativehumidity_2m", [])[:6],
                    hourly.get("windspeed_10m", [])[:6],
                ):
                    tstamp = tt.split("T")[-1]
                    lines.append(f"  {tstamp}: {tp}°C, RH {hm}%, Wind {ws} m/s")

            return "\n".join(lines)

        # -------- Current + forecast (default) --------
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "current_weather": "true",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,precipitation",
        }
        r = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        cw = data.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")

        summary = f"🌤 Weather in {name}: {_format_temp(temp)}, wind {wind} m/s."

        if detail:
            daily = data.get("daily", {})
            lines = [f"🌍 Detailed weather for {name}:"]
            lines.append(f"• Current: {_format_temp(temp)}, Wind {wind} m/s, Code {cw.get('weathercode')}")

            # Next 3 days
            for d, tmin, tmax, p in zip(
                daily.get("time", [])[:3],
                daily.get("temperature_2m_min", [])[:3],
                daily.get("temperature_2m_max", [])[:3],
                daily.get("precipitation_sum", [])[:3],
            ):
                lines.append(f"• {d}: {_format_val(tmin)}°C — {_format_val(tmax)}°C, precip {_format_val(p)} mm")

            # Hourly snapshot
            hourly = data.get("hourly", {})
            lines.append("\n🕒 Hourly (next 6h):")
            for tt, tp, hm, ws in zip(
                hourly.get("time", [])[:6],
                hourly.get("temperature_2m", [])[:6],
                hourly.get("relativehumidity_2m", [])[:6],
                hourly.get("windspeed_10m", [])[:6],
            ):
                tstamp = tt.split("T")[-1]
                lines.append(f"  {tstamp}: {tp}°C, RH {hm}%, Wind {ws} m/s")

            return "\n".join(lines)

        return summary

    except requests.HTTPError as he:
        return f"⚠️ Weather API error: {he}"
    except Exception as e:
        return f"⚠️ Weather error: {e}"
