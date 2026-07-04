import ticketmaster_client
import config

def test_mock_ticketmaster_details():
    details = ticketmaster_client.get_ticketmaster_event_details("Fred again..", "Washington", test_mode=True)
    assert details is not None
    assert details["face_value_min"] == 75.0
    assert details["face_value_max"] == 95.0
    assert details["onsale_date"] == "2026-07-15T10:00:00"
