import requests
import logging
import config
import time
import threading

logger = logging.getLogger(__name__)

# Thread-safe rate limiter to respect Ticketmaster's limit of 5 requests per second
_last_request_time = 0.0
_rate_limit_lock = threading.Lock()

def get_ticketmaster_event_details(artist_name: str, venue_city: str) -> dict:
    global _last_request_time
    if not getattr(config, 'TICKETMASTER_API_KEY', None):
        return None
        
    # Rate limit: space requests by at least 300ms (max ~3 requests/second)
    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
        _last_request_time = time.time()
    
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": config.TICKETMASTER_API_KEY,
        "keyword": artist_name,
        "city": venue_city,
        "classificationName": "dance",
        "size": 1
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        events = (data.get("_embedded") or {}).get("events", [])
        if not events:
            return None
        
        event = events[0]
        price_ranges = event.get("priceRanges") or []
        face_min = price_ranges[0].get("min") if price_ranges else None
        face_max = price_ranges[0].get("max") if price_ranges else None
        
        onsales = (event.get("sales") or {}).get("public") or {}
        onsale_date = onsales.get("startDateTime")
        
        return {
            "face_value_min": face_min,
            "face_value_max": face_max,
            "onsale_date": onsale_date,
            "ticketmaster_url": event.get("url")
        }
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"Error querying Ticketmaster for {artist_name}: {e}")
        return None
