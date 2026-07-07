from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PriceRange:
    min_price: float
    max_price: float
    currency: str
    type: str

@dataclass
class EventPricing:
    event_id: str
    platform: str
    prices: List[PriceRange]
    url: Optional[str] = None
