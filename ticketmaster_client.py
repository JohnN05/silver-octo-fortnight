import requests
import logging
import config

logger = logging.getLogger(__name__)

def mock_ticketmaster_event_details(artist_name):
    if "Fred again" in artist_name:
        return {
            "face_value_min": 75.0,
            "face_value_max": 95.0,
            "onsale_date": "2026-07-15T10:00:00",
            "ticketmaster_url": "https://www.ticketmaster.com/mock-fred-again"
        }
    elif "John Summit" in artist_name:
        return {
            "face_value_min": 45.0,
            "face_value_max": 65.0,
            "onsale_date": "2026-07-10T12:00:00",
            "ticketmaster_url": "https://www.ticketmaster.com/mock-john-summit"
        }
    return None

def get_ticketmaster_event_details(artist_name, venue_city, test_mode=False):
    if test_mode or not getattr(config, 'TICKETMASTER_API_KEY', None):
        return mock_ticketmaster_event_details(artist_name)
    
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
        events = data.get("_embedded", {}).get("events", [])
        if not events:
            return None
        
        event = events[0]
        price_ranges = event.get("priceRanges") or []
        face_min = price_ranges[0].get("min") if price_ranges else None
        face_max = price_ranges[0].get("max") if price_ranges else None
        
        onsales = event.get("sales", {}).get("public", {})
        onsale_date = onsales.get("startDateTime")
        
        return {
            "face_value_min": face_min,
            "face_value_max": face_max,
            "onsale_date": onsale_date,
            "ticketmaster_url": event.get("url")
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Ticketmaster for {artist_name}: {e}")
        return None
