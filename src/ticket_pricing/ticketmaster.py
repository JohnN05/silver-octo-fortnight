# src/ticket_pricing/ticketmaster.py
import logging
from apify_client import ApifyClient
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing, PriceRange

logger = logging.getLogger(__name__)

class ApifyTicketmasterClient(BaseTicketClient):
    # We use a popular, reliable Apify actor for Ticketmaster scraping
    ACTOR_ID = "parseforge/ticketmaster-scraper"

    def __init__(self, api_token: str) -> None:
        self.client = ApifyClient(api_token)

    def get_event_prices(self, event_url: str) -> EventPricing:
        # Prepare the Actor input
        run_input = {
            "startUrls": [{"url": event_url}],
            "maxItems": 100,
            "includeResale": False
        }

        try:
            # Run the Actor and wait for it to finish
            run = self.client.actor(self.ACTOR_ID).call(run_input=run_input, memory_mbytes=128)

            # Fetch results from the dataset
            if isinstance(run, dict):
                dataset_id = run.get("defaultDatasetId")
            elif hasattr(run, "default_dataset_id"):
                dataset_id = run.default_dataset_id
            elif hasattr(run, "dict"):
                dataset_id = run.dict().get("default_dataset_id") or run.dict().get("defaultDatasetId")
            else:
                dataset_id = getattr(run, "defaultDatasetId", None)

            prices = []
            for item in self.client.dataset(dataset_id).iterate_items():
                # 1. Parse using tickets dictionary (parseforge schema)
                tickets = item.get("tickets")
                if isinstance(tickets, dict):
                    min_p = tickets.get("minPrice")
                    max_p = tickets.get("maxPrice")
                    currency = tickets.get("currency") or item.get("currency") or "USD"
                    is_resale = (
                        item.get("isResale")
                        or tickets.get("isResale")
                        or "resale" in (item.get("type") or "").lower()
                        or "resale" in (tickets.get("type") or "").lower()
                    )
                    if not is_resale:
                        if min_p is not None:
                            try:
                                min_val = float(min_p)
                                max_val = float(max_p) if max_p is not None else min_val
                                prices.append(
                                    PriceRange(
                                        min_price=min_val,
                                        max_price=max_val,
                                        currency=currency,
                                        type="Standard Ticket"
                                    )
                                )
                                continue  # successfully parsed via new schema
                            except (ValueError, TypeError):
                                pass

                # 2. Fallback to old flat schema
                if item.get("isResale") or "resale" in (item.get("type") or "").lower():
                    continue

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
                        type=item.get("type") or "Standard Ticket"
                    )
                )
                
            return EventPricing(
                event_id=event_url,
                platform="ticketmaster",
                prices=prices,
                url=event_url
            )
        except Exception:
            logger.error("Apify error", exc_info=True)
            return EventPricing(
                event_id=event_url,
                platform="ticketmaster",
                prices=[],
                url=event_url
            )
