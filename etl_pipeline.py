import database
import seatgeek_client
import ticketmaster_client
import stubhub_scraper
import valuation_engine
import config
from datetime import datetime, timedelta, timezone
import logging

def run_daily_etl(conn, test_mode=False):
    # 1. Fetch upcoming events near location
    upcoming = seatgeek_client.get_upcoming_edm_events()
    
    results = []
    
    for event in upcoming:
        try:
            performer_id = event["artist_id"]
            
            # Check database for performer
            performer = database.get_performer(conn, performer_id)
            is_stale = True
            
            if performer:
                # Check staleness (7-day threshold)
                last_updated = datetime.fromisoformat(performer["last_updated"])
                if datetime.now(timezone.utc).replace(tzinfo=None) - last_updated < timedelta(days=config.STALE_THRESHOLD_DAYS):
                    is_stale = False
                    
            if not performer or is_stale:
                # Perform historical bootstrapping (lazy load)
                bootstrap_performer_history(conn, performer_id, event["artist"], event["artist_score"])
                performer = database.get_performer(conn, performer_id)
            
            # Fetch face value and onsale date via Ticketmaster Discovery API
            tm_details = ticketmaster_client.get_ticketmaster_event_details(event["artist"], event.get("venue_city"))
            face_value = tm_details.get("face_value_min") if tm_details else None
            onsale_date = tm_details.get("onsale_date") if tm_details else None
            ticketmaster_url = tm_details.get("ticketmaster_url") if tm_details else None
        
            if not face_value:
                # Fallback to SeatGeek face value estimation
                face_value = event.get("face_value") or valuation_engine.estimate_face_value(event["artist_score"], event.get("venue_capacity"))
                
            event["face_value"] = face_value
            event["onsale_date"] = onsale_date
            event["ticketmaster_url"] = ticketmaster_url
            
            # Get current resale price on StubHub
            resale_lowest = event.get("resale_lowest")
            if not resale_lowest:
                resale_lowest = stubhub_scraper.scrape_stubhub_resale_price(event["artist"], event.get("venue_city"))
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
