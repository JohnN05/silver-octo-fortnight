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

def estimate_face_value(artist_score: float, venue_capacity: int = None) -> float:
    """
    Estimates ticket face value based on artist score and venue capacity.
    """
    # Set base price based on score
    if artist_score < 0.45:
        base_price = 30.0
    elif artist_score < 0.65:
        base_price = 45.0
    else:
        base_price = 75.0
        
    # Adjust price for venue capacity tier
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
