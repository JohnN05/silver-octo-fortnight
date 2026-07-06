import datetime
from datetime import timezone

def is_stale(last_updated: str, threshold_days: int) -> bool:
    """Checks if the cached data is older than the threshold."""
    if not last_updated:
        return True
    
    try:
        updated_date = datetime.datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.datetime.now(timezone.utc)
        return (now - updated_date).days >= threshold_days
    except ValueError:
        return True

def estimate_face_value(artist_score: float, venue_capacity: int = None, venue_name: str = None) -> float:
    """
    Estimates ticket face value based on artist score, venue capacity, and venue.
    """
    # 1. If we have a known premium venue, apply venue-specific estimation logic
    if venue_name:
        name_lower = venue_name.lower()
        if "echostage" in name_lower:
            # Echostage baseline includes fees (~$12 for TM)
            if artist_score < 0.45:
                return 47.0
            elif artist_score < 0.65:
                return 55.0
            else:
                return 85.0
        elif "anthem" in name_lower:
            if artist_score < 0.45:
                return 50.0
            elif artist_score < 0.65:
                return 65.0
            else:
                return 95.0
        elif "pier six" in name_lower or "power plant" in name_lower:
            if artist_score < 0.45:
                return 45.0
            elif artist_score < 0.65:
                return 55.0
            else:
                return 80.0
        elif "soundcheck" in name_lower or "flash" in name_lower:
            if artist_score < 0.45:
                return 25.0
            elif artist_score < 0.65:
                return 35.0
            else:
                return 45.0

    # 2. Fallback to default heuristic based on popularity score & capacity
    if artist_score < 0.45:
        base_price = 30.0
    elif artist_score < 0.65:
        base_price = 45.0
    else:
        base_price = 75.0
        
    if venue_capacity is not None:
        try:
            v_cap = int(venue_capacity)
            if v_cap > 10000:
                # Arena premium
                base_price += 15.0
            elif v_cap <= 3000:
                # Club discount
                base_price = max(base_price - 5.0, 25.0)
        except (ValueError, TypeError):
            pass
        
    return base_price
