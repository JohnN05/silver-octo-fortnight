import pytest
import requests
import config
from unittest.mock import patch, MagicMock
import ticketmaster_client
from ticket_pricing.ticketmaster import ScraperApiTicketmasterClient

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

@patch('ticket_pricing.ticketmaster.requests.get')
def test_scraper_api_ticketmaster_client_success(mock_get):
    html_content = """
    <html>
        <body>
            <script type="application/ld+json">
            {
                "@type": "MusicEvent",
                "offers": {
                    "@type": "AggregateOffer",
                    "lowPrice": "45.50",
                    "highPrice": "150.00",
                    "priceCurrency": "USD"
                }
            }
            </script>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    client = ScraperApiTicketmasterClient(api_key="test_scraper_key")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert pricing.platform == "ticketmaster"
    assert len(pricing.prices) == 1
    assert pricing.prices[0].min_price == 45.50
    assert pricing.prices[0].max_price == 150.00
    assert pricing.prices[0].currency == "USD"
    mock_get.assert_called_once()

@patch('ticket_pricing.ticketmaster.requests.get')
def test_scraper_api_ticketmaster_client_no_prices(mock_get):
    html_content = "<html><body></body></html>"
    mock_response = MagicMock()
    mock_response.text = html_content
    mock_get.return_value = mock_response

    client = ScraperApiTicketmasterClient(api_key="test_scraper_key")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert len(pricing.prices) == 0

@patch('ticket_pricing.ticketmaster.requests.get')
def test_scraper_api_ticketmaster_client_error(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("API Error")
    
    client = ScraperApiTicketmasterClient(api_key="test_scraper_key")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert len(pricing.prices) == 0
