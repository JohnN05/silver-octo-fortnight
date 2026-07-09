# src/ticket_pricing/ticketmaster.py
import logging
import requests
import json
from bs4 import BeautifulSoup
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing, PriceRange

logger = logging.getLogger(__name__)

class ScraperApiTicketmasterClient(BaseTicketClient):
    # Uses ScraperAPI to bypass bot protection and extract JSON-LD offers
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "http://api.scraperapi.com"

    def get_event_prices(self, event_url: str) -> EventPricing:
        payload = {
            'api_key': self.api_key,
            'url': event_url,
            'render': 'true',  # TM requires JS rendering
            'country_code': 'us'
        }
        
        try:
            response = requests.get(self.base_url, params=payload, timeout=60)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            prices = []
            
            # Find JSON-LD script tags
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if not script.string:
                    continue
                try:
                    data = json.loads(script.string)
                    # Handle if data is a list
                    if isinstance(data, list):
                        items = data
                    else:
                        items = [data]
                        
                    for item in items:
                        if item.get('@type') in ('Event', 'MusicEvent', 'TheaterEvent', 'SportsEvent', 'ComedyEvent', 'DanceEvent', 'Festival'):
                            offers = item.get('offers')
                            if not offers:
                                continue
                            if isinstance(offers, dict):
                                offers = [offers]
                            
                            for offer in offers:
                                price = offer.get('price')
                                low_price = offer.get('lowPrice')
                                high_price = offer.get('highPrice')
                                currency = offer.get('priceCurrency', 'USD')
                                
                                # If it's an AggregateOffer it might have lowPrice
                                if offer.get('@type') == 'AggregateOffer':
                                    min_val = float(low_price) if low_price is not None else None
                                    max_val = float(high_price) if high_price is not None else min_val
                                    if min_val is not None:
                                        prices.append(
                                            PriceRange(
                                                min_price=min_val,
                                                max_price=max_val,
                                                currency=currency,
                                                type="AggregateOffer"
                                            )
                                        )
                                else:
                                    if price is not None:
                                        try:
                                            p = float(price)
                                            prices.append(
                                                PriceRange(
                                                    min_price=p,
                                                    max_price=p,
                                                    currency=currency,
                                                    type="Standard Ticket"
                                                )
                                            )
                                        except (ValueError, TypeError):
                                            pass
                except json.JSONDecodeError:
                    pass

            return EventPricing(
                event_id=event_url,
                platform="ticketmaster",
                prices=prices,
                url=event_url
            )
        except Exception:
            logger.error("ScraperAPI error", exc_info=True)
            return EventPricing(
                event_id=event_url,
                platform="ticketmaster",
                prices=[],
                url=event_url
            )
