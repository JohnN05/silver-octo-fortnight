import urllib.parse
import requests
from bs4 import BeautifulSoup
import logging
import re

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

def scrape_stubhub_resale_price(artist_name, venue_city=""):
    """
    Attempts to scrape StubHub search results for the lowest ticket price.
    Uses browser headers, but falls back gracefully to None if blocked by Akamai/Cloudflare.
    """
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
