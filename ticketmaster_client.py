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

import re

def scrape_ticketmaster_price(url: str) -> float:
    """
    Attempts to scrape the true face value from a Ticketmaster event page using ScraperAPI
    to bypass Akamai WAF.
    """
    if not getattr(config, 'SCRAPER_API_KEY', None) or not url:
        return None
        
    payload = {
        'api_key': config.SCRAPER_API_KEY,
        'url': url,
        'antibot': 'true'  # Recommended for highly protected sites like Ticketmaster
    }
    
    logger.info(f"Attempting to scrape Ticketmaster face value via ScraperAPI for: {url}")
    try:
        response = requests.get('https://api.scraperapi.com/', params=payload, timeout=45)
        if response.status_code == 200:
            content = response.text
            
            # Attempt to parse minPrice from __INITIAL_STATE__ or generic JSON in the page
            prices = re.findall(r'"minPrice"\s*:\s*([0-9.]+)', content)
            if prices:
                valid_prices = [float(p) for p in prices if float(p) > 5]
                if valid_prices:
                    val = min(valid_prices)
                    logger.info(f"Found Ticketmaster minPrice: ${val}")
                    return val
            
            # Fallback to scanning for faceValue
            face_values = re.findall(r'"faceValue"\s*:\s*([0-9.]+)', content)
            if face_values:
                valid_fv = [float(p) for p in face_values if float(p) > 5]
                if valid_fv:
                    val = min(valid_fv)
                    logger.info(f"Found Ticketmaster faceValue: ${val}")
                    return val
                    
            logger.info(f"ScraperAPI fetched page but found no price data in HTML.")
        else:
            logger.warning(f"ScraperAPI returned status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error scraping Ticketmaster with ScraperAPI: {e}")
        
    return None
