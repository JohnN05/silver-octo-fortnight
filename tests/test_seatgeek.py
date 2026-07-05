import pytest
from unittest.mock import patch, MagicMock
import requests
import seatgeek_client
from typing import List, Dict, Any

def test_seatgeek_parsed_fields():
    # We override the return data or inspect parsing
    # Let's verify that key venue city keys are present
    dummy_event = {
        "performers": [{"name": "Test DJ", "id": 9999, "score": 0.8, "genres": [{"slug": "electronic", "primary": True}]}],
        "venue": {"name": "Echo Club", "city": "Gaithersburg", "state": "MD"},
        "stats": {"lowest_price": 40.0, "highest_price": 100.0, "average_price": 60.0, "listing_count": 10},
        "datetime_local": "2026-08-15T21:00:00",
        "url": "https://seatgeek.com/mock-event",
        "id": 12345,
        "title": "Test DJ at Echo Club"
    }

    # Mock requests.get
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": [dummy_event]}
        mock_get.return_value = mock_response

        # Mock config
        with patch('config.SEATGEEK_CLIENT_ID', 'test_id'), \
             patch('config.POPULARITY_THRESHOLD', 0.5):
            
            events = seatgeek_client.get_upcoming_edm_events()
            
            assert len(events) == 1
            parsed = events[0]
            assert parsed["venue_name"] == "Echo Club"
            assert parsed["venue_city"] == "Gaithersburg"
            assert parsed["venue_state"] == "MD"
            assert parsed["venue"] == "Echo Club (Gaithersburg, MD)"

@patch('config.SEATGEEK_CLIENT_ID', 'test_id')
@patch('requests.get')
def test_get_upcoming_edm_events_success(mock_get):
    dummy_event = {
        "performers": [{"name": "Test DJ", "id": 9999, "score": 0.8, "genres": [{"slug": "electronic", "primary": True}]}],
        "venue": {"name": "Echo Club", "city": "Gaithersburg", "state": "MD"},
        "stats": {"lowest_price": 40.0, "highest_price": 100.0, "average_price": 60.0, "listing_count": 10},
        "datetime_local": "2026-08-15T21:00:00",
        "url": "https://seatgeek.com/mock-event",
        "id": 12345,
        "title": "Test DJ at Echo Club"
    }

    mock_response = MagicMock()
    mock_response.json.return_value = {"events": [dummy_event]}
    mock_get.return_value = mock_response

    with patch('config.POPULARITY_THRESHOLD', 0.5):
        events = seatgeek_client.get_upcoming_edm_events()
        assert len(events) == 1
        assert events[0]["id"] == 12345
        assert events[0]["artist"] == "Test DJ"

@patch('config.SEATGEEK_CLIENT_ID', 'test_id')
@patch('requests.get')
def test_get_upcoming_edm_events_request_exception(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("API down")
    
    events = seatgeek_client.get_upcoming_edm_events()
    assert events == []

@patch('config.SEATGEEK_CLIENT_ID', 'test_id')
@patch('requests.get')
def test_get_upcoming_edm_events_value_error(mock_get):
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response
    
    events = seatgeek_client.get_upcoming_edm_events()
    assert events == []

@patch('config.SEATGEEK_CLIENT_ID', 'test_id')
@patch('requests.get')
def test_get_performer_resale_average_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [
            {"stats": {"lowest_price": 50.0}},
            {"stats": {"lowest_price": 100.0}}
        ]
    }
    mock_get.return_value = mock_response
    
    avg = seatgeek_client.get_performer_resale_average(9999)
    assert avg == 75.0

@patch('config.SEATGEEK_CLIENT_ID', 'test_id')
@patch('requests.get')
def test_get_performer_resale_average_no_id(mock_get):
    avg = seatgeek_client.get_performer_resale_average(None)
    assert avg is None
    mock_get.assert_not_called()

@patch('config.SEATGEEK_CLIENT_ID', 'test_id')
@patch('requests.get')
def test_get_performer_resale_average_exception(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("API down")
    avg = seatgeek_client.get_performer_resale_average(9999)
    assert avg is None
