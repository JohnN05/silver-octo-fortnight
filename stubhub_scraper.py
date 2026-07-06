import urllib.parse
import requests
from bs4 import BeautifulSoup
import logging
import re
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_stubhub_search_url(artist_name, venue_city=""):
    """
    Generates a clickable StubHub search URL for the user to check prices directly.
    """
    # Clean queries of special characters like dots that break searches
    clean_artist = re.sub(r'[^\w\s-]', '', artist_name).strip()
    clean_city = re.sub(r'[^\w\s-]', '', venue_city).strip() if venue_city else ""
    
    query = f"{clean_artist} {clean_city}".strip()
    encoded_query = urllib.parse.quote(query)
    return f"https://www.stubhub.com/secure/search?q={encoded_query}"

def scrape_tickpick_resale_price(artist_name, venue_city="", event_date=None):
    """
    Scrapes TickPick search results for the lowest ticket price.
    TickPick is more scrapable than StubHub and does not block simple requests.
    """
    # Query just the artist name to find the performer on TickPick
    url = f"https://www.tickpick.com/search/?q={urllib.parse.quote(artist_name)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        logger.info(f"Attempting to query TickPick search for: {artist_name}")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"TickPick returned status code {response.status_code} for query: {artist_name}")
            return None
            
        # Extract Next.js streams
        scripts = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\s*\]\)', response.text)
        full_stream = "".join(s.replace(r'\"', '"').replace(r'\\', '\\') for s in scripts)
        
        parsed_events = []
        for m in re.finditer(r'"event_id":"([0-9]+)"', full_stream):
            idx = m.start()
            sub = full_stream[idx - 1 : idx + 1000]
            brace_idx = sub.find('}')
            if brace_idx != -1:
                json_str = "{" + sub[1:brace_idx+1]
                try:
                    ev = json.loads(json_str)
                    if "event_name" in ev and "min_price" in ev:
                        parsed_events.append(ev)
                except Exception:
                    pass
                    
        # Filter matching events
        best_match = None
        for ev in parsed_events:
            ev_name = ev.get("event_name", "").lower()
            ev_city = ev.get("city", "").lower()
            ev_venue = ev.get("venue_name", "").lower()
            ev_date_str = ev.get("event_date", "")
            
            # Match performer name
            clean_artist = re.sub(r'[^\w\s]', '', artist_name).lower()
            clean_ev_name = re.sub(r'[^\w\s]', '', ev_name).lower()
            
            is_artist_match = (clean_artist in clean_ev_name or
                               (artist_name.lower() == "dj diesel" and "diesel" in clean_ev_name))
                               
            if not is_artist_match:
                continue
                
            # Match city or venue name
            if venue_city:
                clean_city = re.sub(r'[^\w\s]', '', venue_city).lower()
                if clean_city not in ev_city and clean_city not in ev_venue:
                    continue
                    
            # Match date if provided
            if event_date:
                try:
                    dt_ev = datetime.fromisoformat(ev_date_str.split('T')[0]).date()
                    dt_tgt = datetime.fromisoformat(event_date.split('T')[0]).date()
                    if dt_ev != dt_tgt:
                        continue
                except Exception:
                    pass
                    
            best_match = ev
            break
            
        if best_match:
            price = best_match.get("min_price")
            logger.info(f"Found TickPick price for {artist_name} in {venue_city}: ${price}")
            return float(price) if price is not None else None
            
        # Fallback without date filtering
        for ev in parsed_events:
            ev_name = ev.get("event_name", "").lower()
            ev_city = ev.get("city", "").lower()
            ev_venue = ev.get("venue_name", "").lower()
            
            clean_artist = re.sub(r'[^\w\s]', '', artist_name).lower()
            clean_ev_name = re.sub(r'[^\w\s]', '', ev_name).lower()
            
            is_artist_match = (clean_artist in clean_ev_name or
                               (artist_name.lower() == "dj diesel" and "diesel" in clean_ev_name))
            if not is_artist_match:
                continue
                
            if venue_city:
                clean_city = re.sub(r'[^\w\s]', '', venue_city).lower()
                if clean_city not in ev_city and clean_city not in ev_venue:
                    continue
                    
            price = ev.get("min_price")
            logger.info(f"Found fallback TickPick price for {artist_name} in {venue_city}: ${price}")
            return float(price) if price is not None else None
            
    except Exception as e:
        logger.warning(f"TickPick scraping failed: {e}")
        
    return None

def scrape_stubhub_resale_price(artist_name, venue_city="", event_date=None):
    """
    Attempts to scrape resale prices, checking TickPick first, then falling back to StubHub.
    Uses browser headers, but falls back gracefully to None if blocked by Akamai/Cloudflare.
    """
    # 1. Try TickPick first (high success rate, low blocking)
    price = scrape_tickpick_resale_price(artist_name, venue_city, event_date)
    if price is not None:
        return price
        
    # 2. Fall back to StubHub
    search_url = get_stubhub_search_url(artist_name, venue_city)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    logger.info(f"Attempting to query StubHub search for: {artist_name} in {venue_city}")
    
    try:
        # StubHub's bot protection (Akamai) is very strong. We set a small timeout and catch errors.
        response = requests.get(search_url, headers=headers, timeout=5)
        
        if response.status_code == 403:
            logger.warning("Access to StubHub was blocked (403 Forbidden). StubHub bot protection is active.")
            return None
            
        if response.status_code != 200:
            logger.warning(f"StubHub returned status code: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Method 1: Look for __INITIAL_STATE__ script tag which contains structured JSON data
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "__INITIAL_STATE__" in script.string:
                # Extract pricing patterns from initial state JSON using regex
                # e.g., "minPrice": 85 or similar fields
                min_price_match = re.search(r'"minPrice"\s*:\s*([0-9.]+)', script.string)
                if min_price_match:
                    price = float(min_price_match.group(1))
                    logger.info(f"Found lowest price in StubHub initial state JSON: ${price}")
                    return price
        
        # Method 2: Look for currency/price strings in specific DOM elements
        # Find all elements that likely contain a price
        price_elements = soup.find_all(class_=re.compile(r'price|amount|cost', re.I))
        prices = []
        for el in price_elements:
            text = el.get_text()
            matches = re.findall(r'\$\s*([0-9]{1,4})(?!\d)', text)
            for m in matches:
                if float(m) > 5:
                    prices.append(float(m))
                    
        # If specific classes failed, fallback to scanning entire text but restrict pattern
        if not prices:
            text_content = soup.get_text()
            matches = re.findall(r'(?:price|tickets? from)\s*\$\s*([0-9]{1,4})(?!\d)', text_content, re.I)
            for m in matches:
                if float(m) > 5:
                    prices.append(float(m))

        if prices:
            min_price = min(prices)
            logger.info(f"Parsed lowest price from StubHub text: ${min_price}")
            return min_price
                
        logger.info("No prices could be parsed from StubHub search page HTML.")
        return None
        
    except Exception as e:
        logger.warning(f"StubHub scraping failed or timed out: {e}")
        return None

if __name__ == "__main__":
    # Test scraping stub
    price = scrape_stubhub_resale_price("Martin Garrix", "Washington")
    print(f"Scraped Price: {price}")
    print(f"Search URL: {get_stubhub_search_url('Martin Garrix', 'Washington')}")
