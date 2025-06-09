# google_utils.py

import os, json, requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import time
load_dotenv()

API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CX_ID   = os.getenv("GOOGLE_SEARCH_CX")          # Custom-search engine ID

if not API_KEY or not CX_ID:
    raise ValueError("Missing GOOGLE_SEARCH_API_KEY or GOOGLE_SEARCH_CX in .env")



def _rate_limit_guard(metrics_entry) -> None:
    """Respects per-minute quota for google searches."""
    rate_limit = metrics_entry.data.get("rate_limit_per_minute", 100)
    while True:
        now = datetime.now(timezone.utc)
        minute_key = now.strftime("%Y-%m-%dT%H:%M")
        req_map = metrics_entry.data.setdefault("search_requests_made", {})
        made_this_minute = req_map.get(minute_key, 0)

        if made_this_minute < rate_limit:
            req_map[minute_key] = made_this_minute + 1
            metrics_entry.data["available_searches_now_per_minute"] = (
                rate_limit - req_map[minute_key]
            )
            return
        time.sleep(60 - now.second + 0.1)

def google_search(query: str, api_key: str, cx: str, num: int = 10) -> list[dict]:
    """
    Call Google Custom Search JSON API and return a list of result dicts.
    """
    endpoint = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx":  CX_ID,
        "q":   query,
        "num": min(num, 10)          # Google allows up to 10 per request
    }
    r = requests.get(endpoint, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title":    item.get("title", ""),
            "url":      item.get("link", ""),
            "snippet":  item.get("snippet", ""),
        })

    print("-------------results-------------------")
    print(results)

    return results