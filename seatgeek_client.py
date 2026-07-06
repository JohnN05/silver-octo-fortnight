import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_upcoming_edm_events() -> List[Dict[str, Any]]:
    """
    Fetches upcoming EDM events within the radius of the target location from SeatGeek.
    Filters for electronic music genre and performers exceeding the popularity threshold.
    """
    url = "https://api.seatgeek.com/2/events"
    
    # Calculate date range (e.g., today to 60 days from now)
    start_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    end_date = (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S")
    
    params = {
        "client_id": config.SEATGEEK_CLIENT_ID,
        "client_secret": config.SEATGEEK_CLIENT_SECRET,
        "lat": config.LATITUDE,
        "lon": config.LONGITUDE,
        "range": config.RADIUS,
        "taxonomies.name": "concert",
        "genres.slug": "electronic",  # SeatGeek tag for EDM/Electronic
        "datetime_utc.gt": start_date,
        "datetime_utc.lte": end_date,
        "per_page": 50,
        "sort": "datetime_local.asc"
    }
    
    logger.info(f"Fetching events from SeatGeek near {config.LATITUDE}, {config.LONGITUDE} within {config.RADIUS}...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        events = data.get("events") or []
        logger.info(f"Retrieved {len(events)} electronic music events.")
        
        valuable_events = []
        for event in events:
            # Parse main performer popularity and information
            performers = event.get("performers") or []
            if not performers:
                continue
            
            # Find the primary or most popular performer
            primary_performer = performers[0]
            score = primary_performer.get("score") or 0.0 # 0.0 to 1.0
            
            # Check popularity threshold
            if score < config.POPULARITY_THRESHOLD:
                continue

            # Filter out non-EDM/Electronic performers (e.g. Pop artists like Kesha/Hilary Duff)
            genres = primary_performer.get("genres") or []
            primary_genre_slug = None
            has_electronic_genre = False
            
            for g in genres:
                slug = g.get("slug", "").lower()
                is_primary = g.get("primary", False)
                if slug in ["electronic", "techno", "house", "trance", "dubstep", "electro", "dance", "dj"]:
                    has_electronic_genre = True
                if is_primary:
                    primary_genre_slug = slug
            
            # Exclude known non-EDM primary genres
            NON_EDM_GENRES = {
                'pop', 'rock', 'country', 'rap', 'hip-hop', 'r-b', 'indie', 'folk', 
                'latin', 'jazz', 'classical', 'metal', 'reggae', 'soul', 'comedy', 
                'alternative', 'rnb', 'singer-songwriter'
            }
            
            if primary_genre_slug in NON_EDM_GENRES:
                logger.info(f"Skipping performer '{primary_performer.get('name')}' - primary genre is '{primary_genre_slug}' (Non-EDM).")
                continue
                
            if not has_electronic_genre:
                logger.info(f"Skipping performer '{primary_performer.get('name')}' - no electronic/EDM genre tags found.")
                continue
            
            # Get venue details
            venue = event.get("venue") or {}
            venue_name = venue.get("name", "Unknown Venue")
            venue_city = venue.get("city", "Unknown City")
            venue_state = venue.get("state", "Unknown State")
            
            # Extract ticket stats
            stats = event.get("stats") or {}
            lowest_price = stats.get("lowest_price")
            highest_price = stats.get("highest_price")
            average_price = stats.get("average_price")
            listing_count = stats.get("listing_count", 0)
            
            # Try to get face value / original price estimation (if available)
            # SeatGeek sometimes lists a "visible_listing_count" or direct links
            # We will search for face value or set a default estimation.
            # If SeatGeek doesn't provide face value, we can use the lowest_price
            # or try to scrape/estimate it.
            face_value = event.get("original_delivery_fee") # dummy check
            
            integrated = event.get("integrated") or {}
            provider_name = integrated.get("provider_name")
            provider_id = integrated.get("provider_id")
            
            # Prepare event dict
            parsed_event = {
                "id": event.get("id"),
                "title": event.get("title"),
                "artist": primary_performer.get("name"),
                "artist_id": primary_performer.get("id"),
                "artist_score": score,
                "date": event.get("datetime_local"),
                "venue": f"{venue_name} ({venue_city}, {venue_state})",
                "venue_name": venue_name,
                "venue_city": venue_city,
                "venue_state": venue_state,
                "url": event.get("url"),
                "resale_lowest": lowest_price,
                "resale_highest": highest_price,
                "resale_average": average_price,
                "resale_count": listing_count,
                "face_value": face_value,
                "provider_name": provider_name,
                "provider_id": provider_id,
                "announcements": event.get("announcements") or {}
            }
            
            valuable_events.append(parsed_event)
            
        logger.info(f"Filtered down to {len(valuable_events)} valuable events above popularity threshold {config.POPULARITY_THRESHOLD}.")
        return valuable_events
        
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"Error fetching data from SeatGeek: {e}")
        return []

def get_performer_resale_average(artist_id: Optional[int]) -> Optional[float]:
    """
    Fetches up to 5 upcoming events nationwide for the given artist ID
    and calculates the average lowest resale price as a value proxy.
    """
    if not artist_id:
        return None
    url = "https://api.seatgeek.com/2/events"
    params = {
        "client_id": config.SEATGEEK_CLIENT_ID,
        "client_secret": config.SEATGEEK_CLIENT_SECRET,
        "performers.id": artist_id,
        "per_page": 5,
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        events = data.get("events") or []
        
        prices = []
        for e in events:
            stats = e.get("stats") or {}
            lowest = stats.get("lowest_price")
            if lowest:
                prices.append(lowest)
                
        if prices:
            return round(sum(prices) / len(prices), 2)
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.warning(f"Failed to fetch national resale average for performer {artist_id}: {e}")
    return None

if __name__ == "__main__":
    # Test client logic
    import json
    # Use a dummy client ID if not loaded
    if not config.SEATGEEK_CLIENT_ID:
        config.SEATGEEK_CLIENT_ID = "dummy"
    events = get_upcoming_edm_events()
    print(json.dumps(events[:2], indent=2))
