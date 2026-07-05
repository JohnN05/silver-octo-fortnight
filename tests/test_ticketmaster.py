import ticketmaster_client
import config
from unittest.mock import patch
import requests

def test_mock_ticketmaster_details():
    details = ticketmaster_client.get_ticketmaster_event_details("Fred again..", "Washington", test_mode=True)
    assert details is not None
    assert details["face_value_min"] == 75.0
    assert details["face_value_max"] == 95.0
    assert details["onsale_date"] == "2026-07-15T10:00:00"

@patch('ticketmaster_client.requests.get')
def test_real_ticketmaster_happy_path(mock_get):
    config.TICKETMASTER_API_KEY = "test_key"
    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        "_embedded": {
            "events": [
                {
                    "priceRanges": [{"min": 50.0, "max": 100.0}],
                    "sales": {"public": {"startDateTime": "2026-08-01T10:00:00Z"}},
                    "url": "https://ticketmaster.com/event/123"
                }
            ]
        }
    }
    
    details = ticketmaster_client.get_ticketmaster_event_details("Artist", "City", test_mode=False)
    assert details is not None
    assert details["face_value_min"] == 50.0
    assert details["face_value_max"] == 100.0
    assert details["onsale_date"] == "2026-08-01T10:00:00Z"
    assert details["ticketmaster_url"] == "https://ticketmaster.com/event/123"
    
    mock_get.assert_called_once()

@patch('ticketmaster_client.requests.get')
def test_real_ticketmaster_empty_response(mock_get):
    config.TICKETMASTER_API_KEY = "test_key"
    mock_response = mock_get.return_value
    mock_response.json.return_value = {}  # No events found
    
    details = ticketmaster_client.get_ticketmaster_event_details("Artist", "City", test_mode=False)
    assert details is None
    mock_get.assert_called_once()

@patch('ticketmaster_client.requests.get')
def test_real_ticketmaster_error_state(mock_get):
    config.TICKETMASTER_API_KEY = "test_key"
    mock_get.side_effect = requests.exceptions.RequestException("API Error")
    
    details = ticketmaster_client.get_ticketmaster_event_details("Artist", "City", test_mode=False)
    assert details is None
    mock_get.assert_called_once()
