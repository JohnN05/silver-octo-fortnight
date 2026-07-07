import ticketmaster_client
import config
from unittest.mock import patch
import requests

@patch('config.TICKETMASTER_API_KEY', None)
def test_mock_ticketmaster_details():
    details = ticketmaster_client.get_ticketmaster_event_details("Fred again..", "Washington")
    assert details is None

@patch('config.TICKETMASTER_API_KEY', 'test_key')
@patch('ticketmaster_client.requests.get')
def test_real_ticketmaster_happy_path(mock_get):
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
    
    details = ticketmaster_client.get_ticketmaster_event_details("Artist", "City")
    assert details is not None
    assert details["face_value_min"] == 50.0
    assert details["face_value_max"] == 100.0
    assert details["onsale_date"] == "2026-08-01T10:00:00Z"
    assert details["ticketmaster_url"] == "https://ticketmaster.com/event/123"
    
    mock_get.assert_called_once()

@patch('config.TICKETMASTER_API_KEY', 'test_key')
@patch('ticketmaster_client.requests.get')
def test_real_ticketmaster_empty_response(mock_get):
    mock_response = mock_get.return_value
    mock_response.json.return_value = {}  # No events found
    
    details = ticketmaster_client.get_ticketmaster_event_details("Artist", "City")
    assert details is None
    mock_get.assert_called_once()

@patch('config.TICKETMASTER_API_KEY', 'test_key')
@patch('ticketmaster_client.requests.get')
def test_real_ticketmaster_error_state(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("API Error")
    
    details = ticketmaster_client.get_ticketmaster_event_details("Artist", "City")
    assert details is None
    mock_get.assert_called_once()

from unittest.mock import MagicMock
from ticket_pricing.ticketmaster import ApifyTicketmasterClient

def test_get_event_prices_success(mocker):
    # Mock the ApifyClient
    mock_apify = mocker.patch('ticket_pricing.ticketmaster.ApifyClient')
    mock_client_instance = MagicMock()
    mock_apify.return_value = mock_client_instance
    
    # Mock the run and dataset behavior
    mock_client_instance.actor().call.return_value = {"defaultDatasetId": "dataset_123"}
    mock_client_instance.dataset().iterate_items.return_value = [
        {
            "id": "Z7r9jZ1Ae_0",
            "url": "https://ticketmaster.com/event",
            "price": 125.50,
            "currency": "USD",
            "type": "General Admission"
        }
    ]
    
    client = ApifyTicketmasterClient(api_token="test_token")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert pricing.platform == "ticketmaster"
    assert pricing.event_id == "https://ticketmaster.com/event"
    assert len(pricing.prices) == 1
    assert pricing.prices[0].min_price == 125.50
    assert pricing.prices[0].max_price == 125.50

def test_get_event_prices_api_error(mocker):
    mock_apify = mocker.patch('ticket_pricing.ticketmaster.ApifyClient')
    mock_client_instance = MagicMock()
    mock_apify.return_value = mock_client_instance
    
    mock_client_instance.actor().call.side_effect = Exception("API Rate Limit")
    
    client = ApifyTicketmasterClient(api_token="test_token")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert pricing.platform == "ticketmaster"
    assert pricing.event_id == "https://ticketmaster.com/event"
    assert len(pricing.prices) == 0

def test_get_event_prices_invalid_prices(mocker):
    mock_apify = mocker.patch('ticket_pricing.ticketmaster.ApifyClient')
    mock_client_instance = MagicMock()
    mock_apify.return_value = mock_client_instance
    
    mock_client_instance.actor().call.return_value = {"defaultDatasetId": "dataset_123"}
    mock_client_instance.dataset().iterate_items.return_value = [
        {
            "id": "1",
            "url": "https://ticketmaster.com/event",
            "price": None,
            "currency": "USD",
            "type": "General Admission"
        },
        {
            "id": "2",
            "url": "https://ticketmaster.com/event",
            "price": "invalid",
            "currency": "USD",
            "type": "General Admission"
        },
        {
            "id": "3",
            "url": "https://ticketmaster.com/event",
            "price": 50.0,
            "currency": "USD",
            "type": "General Admission"
        }
    ]
    
    client = ApifyTicketmasterClient(api_token="test_token")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert pricing.platform == "ticketmaster"
    assert pricing.event_id == "https://ticketmaster.com/event"
    assert len(pricing.prices) == 1
    assert pricing.prices[0].min_price == 50.0
