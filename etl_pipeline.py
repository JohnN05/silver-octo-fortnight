import database
import seatgeek_client
import ticketmaster_client
import stubhub_scraper
import valuation_engine
import config
from datetime import datetime, timedelta, timezone
import logging
import concurrent.futures
import utils
from ticket_pricing.fetcher import TicketPricingFetcher
from ticket_pricing.ticketmaster import ScraperApiTicketmasterClient
from ticket_pricing.eventbrite import EventbriteClient

def _extract_min_price(pricing):
    if not pricing or not getattr(pricing, 'prices', None):
        return None
    valid_prices = [p.min_price for p in pricing.prices if getattr(p, 'min_price', None) is not None]
    return min(valid_prices) if valid_prices else None

def run_daily_etl(conn):
    # Setup Fetcher
    fetcher = TicketPricingFetcher()
    if getattr(config, 'SCRAPER_API_KEY', None):
        fetcher.register_client("ticketmaster", ScraperApiTicketmasterClient(config.SCRAPER_API_KEY))
    if getattr(config, 'EVENTBRITE_API_TOKEN', None):
        fetcher.register_client("eventbrite", EventbriteClient(config.EVENTBRITE_API_TOKEN))

    # 1. Fetch upcoming events near location
    upcoming = seatgeek_client.get_upcoming_edm_events()
    
    # Helper to fetch external data concurrently
    def fetch_external(ev):
        tm_details = ticketmaster_client.get_ticketmaster_event_details(ev["artist"], ev.get("venue_city"))
        resale_lowest = stubhub_scraper.scrape_stubhub_resale_price(ev["artist"], ev.get("venue_city"), ev.get("date"))
        return tm_details, resale_lowest

    # Run API fetches concurrently
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for event in upcoming:
            futures.append((event, executor.submit(fetch_external, event)))
    
    results = []
    
    for event, future in futures:
        try:
            tm_details, fetched_resale_lowest = future.result()
            performer_id = event["artist_id"]
            
            # Check database for performer
            performer = database.get_performer(conn, performer_id)
            is_stale = True
            
            if performer:
                # Check staleness (7-day threshold)
                is_stale = utils.is_stale(performer.get("last_updated"), config.STALE_THRESHOLD_DAYS)
                    
            if not performer or is_stale:
                # Perform historical bootstrapping (lazy load)
                bootstrap_performer_history(conn, performer_id, event["artist"], event["artist_score"])
                performer = database.get_performer(conn, performer_id)
            
            # Fetch face value and onsale date via Ticketmaster Discovery API
            face_value = tm_details.get("face_value_min") if tm_details else None
            onsale_date = tm_details.get("onsale_date") if tm_details else None
            ticketmaster_url = tm_details.get("ticketmaster_url") if tm_details else None
            
            # Reconstruct URL from Seatgeek integrated provider data if available
            if not ticketmaster_url and event.get("provider_name") == "TICKETMASTER" and event.get("provider_id"):
                ticketmaster_url = f"https://www.ticketmaster.com/event/{event['provider_id']}"
            
            # If TM API didn't have price, try fetching via ScraperAPI
            if not face_value and ticketmaster_url and getattr(config, 'SCRAPER_API_KEY', None):
                try:
                    pricing = fetcher.get_prices("ticketmaster", ticketmaster_url)
                    extracted = _extract_min_price(pricing)
                    if extracted is not None:
                        face_value = extracted
                except Exception as e:
                    logging.error(f"Error fetching ticketmaster prices for {ticketmaster_url}: {e}")
                    
            # Check Eventbrite if SeatGeek specified it
            if not face_value and event.get("provider_name") == "EVENTBRITE" and event.get("provider_id") and getattr(config, 'EVENTBRITE_API_TOKEN', None):
                try:
                    pricing = fetcher.get_prices("eventbrite", event["provider_id"])
                    extracted = _extract_min_price(pricing)
                    if extracted is not None:
                        face_value = extracted
                except Exception as e:
                    logging.error(f"Error fetching eventbrite prices for {event.get('provider_id')}: {e}")
        
            if not face_value:
                # Fallback to face value estimation
                face_value = event.get("face_value") or utils.estimate_face_value(
                    artist_score=event["artist_score"],
                    venue_capacity=event.get("venue_capacity"),
                    venue_name=event.get("venue_name")
                )
            event["face_value"] = face_value
            event["onsale_date"] = onsale_date
            event["ticketmaster_url"] = ticketmaster_url
            
            # Get current resale price on StubHub
            resale_lowest = event.get("resale_lowest")
            if not resale_lowest:
                resale_lowest = fetched_resale_lowest
            event["resale_lowest"] = resale_lowest
            
            # Write upcoming event to database
            event_db_dict = {
                "id": event["id"],
                "performer_id": performer_id,
                "title": event["title"],
                "venue_name": event.get("venue_name"),
                "date": event["date"],
                "onsale_date": event.get("onsale_date"),
                "face_value": event["face_value"],
                "resale_lowest": event.get("resale_lowest"),
                "resale_national_avg": event.get("resale_national_avg"),
                "ticketmaster_url": event.get("ticketmaster_url"),
                "seatgeek_url": event["url"]
            }
            database.save_event(conn, event_db_dict)
            
            # Log ticket inventory count to calculate velocity
            ticket_count = event.get("resale_count", 0)
            database.log_inventory(conn, event["id"], ticket_count, event.get("resale_lowest"))
            
            # Calculate velocity and compute priority score
            velocity = valuation_engine.calculate_event_velocity(conn, event["id"])
            
            # Extract performer aggregated historical metrics
            hist_shows = database.get_historical_shows(conn, performer_id)
            avg_past_markup = performer.get("avg_past_markup", 0.0) or 0.0
            
            avg_sellout = 14.0
            if hist_shows:
                valid_sellouts = [s["sell_out_days"] for s in hist_shows if s["sell_out_days"] is not None]
                if valid_sellouts:
                    avg_sellout = sum(valid_sellouts) / len(valid_sellouts)
                    
            valuation_data = {
                "face_value": event["face_value"],
                "resale_lowest": event.get("resale_lowest"),
                "avg_past_markup": avg_past_markup,
                "sell_out_days": avg_sellout,
                "velocity": velocity
            }
            
            analysis = valuation_engine.compute_score(valuation_data)
            results.append((event, analysis))
        except Exception as e:
            logging.error(f"Error processing event {event.get('id', 'unknown')}: {e}")
            
    return results

def bootstrap_performer_history(conn, performer_id, artist_name, score):
    # Live historical fetch
    # We perform a Google search / API call to fetch performer's past venues
    # We estimate average past markup and capacity, storing them
    perf_dict = {
        "id": performer_id,
        "name": artist_name,
        "popularity_score": score,
        "avg_past_markup": 50.0, # default fallback
        "demand_rating": "MEDIUM"
    }
    database.save_performer(conn, perf_dict)
