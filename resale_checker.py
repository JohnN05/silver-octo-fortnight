import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def estimate_face_value(artist_score, venue_capacity=None):
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
    if venue_capacity and venue_capacity > 10000:
        # Arena premium
        base_price += 15.0
    elif venue_capacity and venue_capacity <= 3000:
        # Club discount
        base_price = max(base_price - 5.0, 25.0)
        
    return base_price

def evaluate_deal(event):
    """
    Evaluates the event ticket deal value.
    Compares face value (actual or estimated) with resale pricing (from SeatGeek or StubHub).
    Returns a dictionary of analysis results:
    - is_high_markup: boolean
    - markup_percentage: float
    - value_rating: string
    - est_face_value: float
    - using_national_avg: boolean
    """
    artist_score = event.get("artist_score", 0.0)
    venue_capacity = event.get("venue_capacity")
    
    # 1. Determine Face Value
    face_val = event.get("face_value")
    if not face_val:
        face_val = estimate_face_value(artist_score, venue_capacity)
        
    # 2. Get best resale price available
    resale_price = event.get("resale_lowest")
    using_national_avg = False
    
    if not resale_price:
        resale_price = event.get("resale_national_avg")
        if resale_price:
            using_national_avg = True
        
    if not resale_price:
        return {
            "is_high_markup": False,
            "markup_percentage": 0.0,
            "value_rating": "NEEDS CHECK (No Resale Data)",
            "est_face_value": face_val,
            "using_national_avg": False
        }
    
    # 3. Calculate markup details
    markup_ratio = resale_price / face_val
    markup_percent = (markup_ratio - 1.0) * 100.0
    is_high_markup = markup_ratio >= config.MARKUP_THRESHOLD
    
    # 4. Formulate overall rating
    if artist_score >= 0.60 and is_high_markup:
        rating = "CRITICAL (High Demand & Markup)"
    elif is_high_markup:
        rating = "HIGH (Resale Markup)"
    elif artist_score >= 0.60:
        rating = "MEDIUM (Popular Artist, Face Value)"
    else:
        rating = "LOW"
        
    return {
        "is_high_markup": is_high_markup,
        "markup_percentage": round(markup_percent, 1),
        "value_rating": rating,
        "est_face_value": face_val,
        "using_national_avg": using_national_avg
    }
