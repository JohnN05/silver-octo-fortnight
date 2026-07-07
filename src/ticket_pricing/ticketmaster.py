# src/ticket_pricing/ticketmaster.py
from apify_client import ApifyClient
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing, PriceRange

class ApifyTicketmasterClient(BaseTicketClient):
    # We use a popular, reliable Apify actor for Ticketmaster scraping
    ACTOR_ID = "katerinah/ticketmaster-scraper"

    def __init__(self, api_token: str):
        self.client = ApifyClient(api_token)

    def get_event_prices(self, event_url: str) -> EventPricing:
        # Prepare the Actor input
        run_input = {
            "startUrls": [{"url": event_url}],
            "maxItems": 100
        }

        try:
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.ACTOR_ID).call(run_input=run_input)

            # Fetch results from the dataset
            prices = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                raw_price = item.get("price")
                if raw_price is None:
                    continue
                try:
                    price_val = float(raw_price)
                except (ValueError, TypeError):
                    continue

                prices.append(
                    PriceRange(
                        min_price=price_val,
                        max_price=price_val,
                        currency=item.get("currency", "USD"),
                        type=item.get("type", "Standard Ticket")
                    )
                )
                
            return EventPricing(
                event_id=event_url,
                platform="ticketmaster",
                prices=prices,
                url=event_url
            )
        except Exception:
            return EventPricing(
                event_id=event_url,
                platform="ticketmaster",
                prices=[],
                url=event_url
            )
