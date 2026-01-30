# scraper/web_scraper.py
import requests
from bs4 import BeautifulSoup
import os
from time import sleep
from typing import List, Dict
import hashlib
from urllib.parse import urljoin

DEFAULT_HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "aqi-history-scraper/1.0 (+contact@example.org)")
}

def _id_from_fields(*parts) -> str:
    import hashlib
    key = "|".join([str(p) for p in parts])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def scrape_station_page_history(url: str, item_selector: str, date_selector: str, value_selector: str, parameter: str = "pm25") -> List[Dict]:
    """
    Generic HTML scraper for a station history page.
    - url: page URL
    - item_selector: CSS selector that matches each row/entry
    - date_selector: selector relative to item to extract date text
    - value_selector: selector relative to item to extract numeric value
    Returns normalized observation dicts (value may be concentration; AQI conversion is separate).
    """
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select(item_selector)
    out = []
    for it in items:
        date_el = it.select_one(date_selector)
        val_el = it.select_one(value_selector)
        if not date_el or not val_el:
            continue
        date_text = date_el.get_text(strip=True)
        value_text = val_el.get_text(strip=True).replace(",", "")
        try:
            val = float(value_text)
        except Exception:
            continue
        obs_id = _id_from_fields(url, date_text, parameter)
        obs = {
            "id": obs_id,
            "source": url.split("//", 1)[-1].split("/", 1)[0],
            "location": url,
            "latitude": None,
            "longitude": None,
            "date_utc": date_text,
            "parameter": parameter,
            "aqi": None,
            "value": val,
            "unit": None,
            "raw": {"snippet": str(it)[:2000]}
        }
        out.append(obs)
    sleep(1.0)
    return out