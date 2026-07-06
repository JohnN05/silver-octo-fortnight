import logging
from datetime import datetime, timezone
import hashlib
import uuid
import database
import config
import seatgeek_client
import ticketmaster_client
import resale_checker
from typing import Dict, Any
import utils

logger = logging.getLogger(__name__)



def get_or_update_performer(conn, performer_id: int, artist_name: str, artist_score: float) -> dict:
    """
    Handles caching of performer data to the database based on the staleness threshold.
    """
    performer = database.get_performer(conn, performer_id)
    threshold = getattr(config, 'STALE_THRESHOLD_DAYS', 7)
    
    if performer and not utils.is_stale(performer.get('last_updated'), threshold):
        logger.info(f"Using cached performer data for {artist_name}")
        return performer
        
    logger.info(f"Performer data for {artist_name} is stale or missing. Fetching new data...")
    avg_markup = seatgeek_client.get_performer_resale_average(performer_id)
    
    performer_dict = {
        "id": performer_id,
        "name": artist_name,
        "popularity_score": artist_score,
        "avg_past_markup": avg_markup,
        "demand_rating": "HIGH" if artist_score >= 0.6 else "MEDIUM" if artist_score >= 0.4 else "LOW"
    }
    database.save_performer(conn, performer_dict)
    
    return database.get_performer(conn, performer_id)

def process_event(conn, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coordinates API clients for a single event.
    """
    artist_name = event.get("artist")
    artist_id = event.get("artist_id")
    artist_score = event.get("artist_score", 0.0)
    venue_city = event.get("venue_city")
    venue_capacity = event.get("venue_capacity")
    
    if artist_id:
        # Intentionally triggering cache update side-effect; ignoring return value
        get_or_update_performer(conn, artist_id, artist_name, artist_score)
        
    tm_details = ticketmaster_client.get_ticketmaster_event_details(artist_name, venue_city)
    if tm_details:
        event["ticketmaster_url"] = tm_details.get("ticketmaster_url")
        event["onsale_date"] = tm_details.get("onsale_date")
        
        face_val_min = tm_details.get("face_value_min")
        if face_val_min is not None:
            event["face_value"] = face_val_min
        else:
            event["face_value"] = utils.estimate_face_value(artist_score, venue_capacity)
    else:
        event["face_value"] = utils.estimate_face_value(artist_score, venue_capacity)
        
    if artist_name and event.get("date"):
        fallback_id = hashlib.md5(f"{artist_name}_{event.get('date')}".encode()).hexdigest()
    else:
        fallback_id = uuid.uuid4().hex
    event_id = event.get("id") or fallback_id
    
    event_record = {
        "id": event_id,
        "performer_id": artist_id,
        "title": event.get("title", f"{artist_name} Concert"),
        "venue_name": event.get("venue_name", "Unknown"),
        "date": event.get("date", "Unknown"),
        "onsale_date": event.get("onsale_date"),
        "face_value": event.get("face_value"),
        "resale_lowest": event.get("resale_lowest"),
        "resale_national_avg": event.get("resale_national_avg"),
        "ticketmaster_url": event.get("ticketmaster_url"),
        "seatgeek_url": event.get("url")
    }
    
    if artist_id:
        database.save_event(conn, event_record)
        
    return event
