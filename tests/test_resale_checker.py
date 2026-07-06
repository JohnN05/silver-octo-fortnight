import resale_checker
import utils

def test_estimate_face_value():
    # Arena show for high popularity artist
    arena_val = utils.estimate_face_value(0.8, venue_capacity=15000)
    assert arena_val == 90.0
    
    # Club show for same artist
    club_val = utils.estimate_face_value(0.8, venue_capacity=1500)
    assert club_val == 70.0

def test_evaluate_deal_passes_capacity():
    # Verify evaluate_deal passes capacity if present
    event = {
        "artist_score": 0.8,
        "venue_capacity": 15000,
        "resale_lowest": 180.0
    }
    result = resale_checker.evaluate_deal(event)
    # estimate_face_value should be 90, resale is 180 -> markup 2.0, so 100% markup
    assert result["est_face_value"] == 90.0
    assert result["markup_percentage"] == 100.0
