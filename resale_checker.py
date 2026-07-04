import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def estimate_face_value(artist_score):
    """
    Estimates the original direct-from-artist ticket face value based on artist popularity.
    This acts as a fallback when the actual face value is not available in the API.
    - Low popularity (<0.45): ~$25 - $35 (Typical club tier)
    - Medium popularity (0.45 - 0.65): ~$35 - $60 (Major club / medium concert hall)
    - High popularity (>0.65): ~$60 - $95+ (Large music hall / arena)
    """
    if artist_score < 0.45:
        return 30.0
    elif artist_score < 0.65:
        return 45.0
    else:
        return 75.0

def evaluate_deal(event):
    """
    Evaluates the event ticket deal value.
    Compares face value (actual or estimated) with resale pricing (from SeatGeek or StubHub).
    Returns a dictionary of analysis results:
    - is_high_markup: boolean
    - markup_percentage: float
    - value_rating: string ('HIGH', 'MEDIUM', 'LOW')
    - est_face_value: float
    """
    artist_score = event.get("artist_score", 0.0)
    
    # 1. Determine Face Value
    face_val = event.get("face_value")
    if not face_val:
        face_val = estimate_face_value(artist_score)
        
    # 2. Get best resale price available
    resale_price = event.get("resale_lowest")
    if not resale_price:
        # If no lowest resale price, we cannot evaluate markup
        return {
            "is_high_markup": False,
            "markup_percentage": 0.0,
            "value_rating": "NEEDS CHECK",
            "est_face_value": face_val
        }
    
    # 3. Calculate markup details
    markup_ratio = resale_price / face_val
    markup_percent = (markup_ratio - 1.0) * 100.0
    is_high_markup = markup_ratio >= config.MARKUP_THRESHOLD
    
    # 4. Formulate overall rating
    # Highly popular artist + high resale markup = HIGH value
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
        "est_face_value": face_val
    }
