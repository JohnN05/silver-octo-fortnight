from typing import Dict
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing

class TicketPricingFetcher:
    def __init__(self):
        self._clients: Dict[str, BaseTicketClient] = {}

    def register_client(self, platform: str, client: BaseTicketClient) -> None:
        self._clients[platform] = client

    def get_prices(self, platform: str, event_id: str) -> EventPricing:
        client = self._clients.get(platform)
        if not client:
            raise ValueError(f"No client registered for platform: {platform}")
        
        return client.get_event_prices(event_id)
