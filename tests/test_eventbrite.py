import pytest
import responses
from ticket_pricing.eventbrite import EventbriteClient

@responses.activate
def test_get_event_prices_success():
    client = EventbriteClient(api_token="test_token")
    event_id = "123456789"
    
    responses.add(
        responses.GET,
        f"https://www.eventbriteapi.com/v3/events/{event_id}/ticket_classes/",
        json={
            "ticket_classes": [
                {
                    "name": "General Admission",
                    "cost": {"value": 5000, "currency": "USD"} # Eventbrite uses minor units
                }
            ]
        },
        status=200
    )
    
    pricing = client.get_event_prices(event_id)
    assert pricing.platform == "eventbrite"
    assert pricing.event_id == event_id
    assert len(pricing.prices) == 1
    assert pricing.prices[0].min_price == 50.0
    assert pricing.prices[0].max_price == 50.0
    assert pricing.prices[0].currency == "USD"
    assert pricing.prices[0].type == "General Admission"

@responses.activate
def test_get_event_prices_rate_limit():
    client = EventbriteClient(api_token="test_token")
    event_id = "123456789"
    
    responses.add(
        responses.GET,
        f"https://www.eventbriteapi.com/v3/events/{event_id}/ticket_classes/",
        status=429
    )
    
    pricing = client.get_event_prices(event_id)
    assert pricing.platform == "eventbrite"
    assert pricing.event_id == event_id
    assert len(pricing.prices) == 0

@responses.activate
def test_get_event_prices_missing_data():
    client = EventbriteClient(api_token="test_token")
    event_id = "123456789"
    
    responses.add(
        responses.GET,
        f"https://www.eventbriteapi.com/v3/events/{event_id}/ticket_classes/",
        json={
            "ticket_classes": [
                {
                    "name": "General Admission"
                },
                {}
            ]
        },
        status=200
    )
    
    pricing = client.get_event_prices(event_id)
    assert pricing.platform == "eventbrite"
    assert pricing.event_id == event_id
    assert len(pricing.prices) == 0
