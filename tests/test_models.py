from ticket_pricing.models import PriceRange, EventPricing

def test_price_range_creation():
    pr = PriceRange(min_price=50.0, max_price=150.0, currency="USD", type="standard")
    assert pr.min_price == 50.0
    assert pr.max_price == 150.0
    assert pr.currency == "USD"
    assert pr.type == "standard"

def test_event_pricing_creation():
    pr = PriceRange(min_price=50.0, max_price=150.0, currency="USD", type="standard")
    ep = EventPricing(event_id="123", platform="ticketmaster", prices=[pr])
    assert ep.event_id == "123"
    assert ep.platform == "ticketmaster"
    assert len(ep.prices) == 1
    assert ep.url is None
