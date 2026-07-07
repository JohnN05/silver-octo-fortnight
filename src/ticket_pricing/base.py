from abc import ABC, abstractmethod
from ticket_pricing.models import EventPricing

class BaseTicketClient(ABC):
    @abstractmethod
    def get_event_prices(self, event_id: str) -> EventPricing:
        pass
