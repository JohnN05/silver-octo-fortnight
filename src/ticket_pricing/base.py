from abc import ABC, abstractmethod
from ticket_pricing.models import EventPricing

class BaseTicketClient(ABC):
    @abstractmethod
    def get_event_prices(self, event_id: str) -> EventPricing:
        """
        Fetch the ticket prices for a given event ID.
        
        Contract:
        - If pricing is missing or unavailable, return an EventPricing object with an empty `prices` list.
        - If rate limits are hit or other network errors occur, raise an appropriate exception so it can be handled globally.
        """
        pass
