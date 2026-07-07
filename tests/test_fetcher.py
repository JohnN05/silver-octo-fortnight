import pytest
from ticket_pricing.fetcher import TicketPricingFetcher
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing, PriceRange

class DummyClient(BaseTicketClient):
    def get_event_prices(self, event_id: str) -> EventPricing:
        return EventPricing(
            event_id=event_id,
            platform="dummy",
            prices=[PriceRange(min_price=10.0, max_price=10.0, currency="USD", type="standard")],
            url="http://dummy"
        )

def test_fetcher_routing():
    fetcher = TicketPricingFetcher()
    fetcher.register_client("dummy", DummyClient())
    
    pricing = fetcher.get_prices("dummy", "123")
    assert pricing.platform == "dummy"
    assert len(pricing.prices) == 1

def test_fetcher_routing_unknown_platform():
    fetcher = TicketPricingFetcher()
    with pytest.raises(ValueError, match="No client registered for platform: unknown"):
        fetcher.get_prices("unknown", "123")
