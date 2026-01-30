# scraper/apis.py
import os
import requests
from typing import List, Dict
from time import sleep
import hashlib
from datetime import datetime

DEFAULT_HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "aqi-history-scraper/1.0 (+contact@example.org)")
}

def _make_id(source: str, location: str, date_utc: str, parameter: str) -> str:
    key = f"{source}|{location}|{date_utc}|{parameter}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

# OpenAQ client (public)
OPENAQ_ENDPOINT = "https://api.openaq.org/v2/measurements"

def fetch_openaq_history(location: str = None, lat: float = None, lon: float = None, start: str = None, end: str = None, parameter: str = None, limit: int = 100) -> List[Dict]:
    """
    Fetch historic measurements from OpenAQ.
    - location: OpenAQ location string OR supply lat/lon and use radius parameters.
    - start/end: ISO date strings (YYYY-MM-DD)
    - parameter: 'pm25', 'pm10', 'o3', 'no2', etc.
    Returns normalized observation dicts.
    """
    params = {"limit": limit, "page": 1}
    if location:
        params["location"] = location
    if parameter:
        params["parameter"] = parameter
    if start:
        params["date_from"] = start
    if end:
        params["date_to"] = end

    results = []
    while True:
        resp = requests.get(OPENAQ_ENDPOINT, params=params, headers=DEFAULT_HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("results", []):
            date_utc = item.get("date", {}).get("utc")
            obs = {
                "id": _make_id("openaq", item.get("location"), date_utc, item.get("parameter")),
                "source": "openaq",
                "location": item.get("location"),
                "latitude": item.get("coordinates", {}).get("latitude"),
                "longitude": item.get("coordinates", {}).get("longitude"),
                "date_utc": date_utc,
                "parameter": item.get("parameter"),
                "aqi": None,  # OpenAQ gives raw concentration; AQI mapping can be computed separately
                "value": item.get("value"),
                "unit": item.get("unit"),
                "raw": item
            }
            results.append(obs)
        meta = data.get("meta", {})
        found = meta.get("found", 0)
        page = meta.get("page", params["page"])
        limit = meta.get("limit", params["limit"])
        # pagination
        if (page * limit) >= found or len(results) >= 2000:
            break
        params["page"] = page + 1
        sleep(0.2)
    return results

# AirNow example client (requires API key)
AIRNOW_ENDPOINT = "https://www.airnowapi.org/aq/observation/latLong/historical/"
AIRNOW_KEY = os.getenv("AIRNOW_API_KEY")

def fetch_airnow_history(lat: float, lon: float, start: str, end: str, distance: int = 25) -> List[Dict]:
    """
    Fetch AirNow historical observations for a lat/lon between start and end (YYYY-MM-DD).
    Note: AirNow returns AQI values directly for parameters (pm25, pm10, o3, etc.). Replace or tune params per API docs.
    """
    if not AIRNOW_KEY:
        raise RuntimeError("AIRNOW_API_KEY not set in environment")
    params = {
        "format": "application/json",
        "latitude": lat,
        "longitude": lon,
        "distance": distance,
        "startDate": f"{start}T00",
        "endDate": f"{end}T23",
        "API_KEY": AIRNOW_KEY
    }
    resp = requests.get(AIRNOW_ENDPOINT, params=params, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data:
        date_utc = item.get("DateObserved") + "T00:00:00Z"  # adjust if API gives time
        obs = {
            "id": _make_id("airnow", f"{lat},{lon}", date_utc, item.get("ParameterName")),
            "source": "airnow",
            "location": item.get("ReportingArea") or f"{lat},{lon}",
            "latitude": lat,
            "longitude": lon,
            "date_utc": date_utc,
            "parameter": item.get("ParameterName"),
            "aqi": item.get("AQI"),
            "value": item.get("ObservedValue"),
            "unit": item.get("Unit") or "AQI",
            "raw": item
        }
        results.append(obs)
    # polite pause
    sleep(0.5)
    return results