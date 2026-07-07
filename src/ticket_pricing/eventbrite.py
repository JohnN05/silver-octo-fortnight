import logging
import requests
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing, PriceRange

logger = logging.getLogger(__name__)

class EventbriteClient(BaseTicketClient):
    BASE_URL = "https://www.eventbriteapi.com/v3"

    def __init__(self, api_token: str):
        self.api_token = api_token

    def get_event_prices(self, event_id: str) -> EventPricing:
        url = f"{self.BASE_URL}/events/{event_id}/ticket_classes/"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                logger.warning(f"Rate limited by Eventbrite API for event {event_id}")
                return EventPricing(
                    event_id=event_id,
                    platform="eventbrite",
                    prices=[],
                    url=f"https://www.eventbrite.com/e/{event_id}"
                )
            raise

        data = response.json()
        
        prices: list[PriceRange] = []
        for tc in data.get("ticket_classes", []):
            cost_info = tc.get("cost")
            if cost_info:
                # Eventbrite provides value in minor units (e.g. cents)
                value = cost_info.get("value", 0) / 100.0
                prices.append(
                    PriceRange(
                        min_price=value,
                        max_price=value,
                        currency=cost_info.get("currency", "USD"),
                        type=tc.get("name", "standard")
                    )
                )
                
        return EventPricing(
            event_id=event_id,
            platform="eventbrite",
            prices=prices,
            url=f"https://www.eventbrite.com/e/{event_id}"
        )
