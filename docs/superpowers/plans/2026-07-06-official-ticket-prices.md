# Official Ticket Prices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular ticket pricing service that reliably retrieves exact, official event face-value prices. It uses the Eventbrite API for Eventbrite events, and leverages the Apify API (via a free-tier scraper actor) to bypass Ticketmaster's anti-bot systems and retrieve exact Ticketmaster pricing without paying for subscriptions or triggering IP bans.

**Architecture:** A Python package with a unified `EventPriceFetcher` interface. It provides two integrations: `ApifyTicketmasterClient` (using the Apify Python SDK to run a Ticketmaster scraper) and `EventbriteClient` (using Eventbrite API to fetch exact `ticket_classes` prices). 

**Tech Stack:** Python 3.10+, `requests`, `apify-client`, `pytest`, `responses`

## Global Constraints

- Must retrieve the exact official face-value ticket price (no resell/heuristics).
- Apify integration must be optimized for low-volume runs (4 times/day) to stay entirely within the free tier.
- Must handle API rate limits and missing pricing gracefully.
- Code must be fully typed and tested.

---

### Task 1: Create Data Models and Base Interface

**Files:**
- Create: `src/ticket_pricing/models.py`
- Create: `src/ticket_pricing/base.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Consumes: None
- Produces: `PriceRange`, `EventPricing`, `BaseTicketClient`

- [ ] **Step 1: Write the failing test for models**

```python
# tests/test_models.py
from ticket_pricing.models import PriceRange, EventPricing

def test_price_range_creation():
    pr = PriceRange(min_price=50.0, max_price=150.0, currency="USD", type="standard")
    assert pr.min_price == 50.0
    assert pr.currency == "USD"

def test_event_pricing_creation():
    pr = PriceRange(min_price=50.0, max_price=150.0, currency="USD", type="standard")
    ep = EventPricing(event_id="123", platform="ticketmaster", prices=[pr])
    assert ep.platform == "ticketmaster"
    assert len(ep.prices) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'ticket_pricing'"

- [ ] **Step 3: Implement data models and base interface**

```python
# src/ticket_pricing/models.py
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
```

```python
# src/ticket_pricing/base.py
from abc import ABC, abstractmethod
from ticket_pricing.models import EventPricing

class BaseTicketClient(ABC):
    @abstractmethod
    def get_event_prices(self, event_id: str) -> EventPricing:
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ticket_pricing/models.py src/ticket_pricing/base.py tests/test_models.py
git commit -m "feat: add domain models and base client interface"
```

### Task 2: Implement Apify Ticketmaster Client

**Files:**
- Create: `src/ticket_pricing/ticketmaster.py`
- Create: `tests/test_ticketmaster.py`

**Interfaces:**
- Consumes: `BaseTicketClient`, `EventPricing`, `PriceRange` from `src/ticket_pricing/models.py`
- Produces: `ApifyTicketmasterClient`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ticketmaster.py
import pytest
from unittest.mock import MagicMock
from ticket_pricing.ticketmaster import ApifyTicketmasterClient

def test_get_event_prices_success(mocker):
    # Mock the ApifyClient
    mock_apify = mocker.patch('ticket_pricing.ticketmaster.ApifyClient')
    mock_client_instance = MagicMock()
    mock_apify.return_value = mock_client_instance
    
    # Mock the run and dataset behavior
    mock_client_instance.actor().call.return_value = {"defaultDatasetId": "dataset_123"}
    mock_client_instance.dataset().iterate_items.return_value = [
        {
            "id": "Z7r9jZ1Ae_0",
            "url": "https://ticketmaster.com/event",
            "price": 125.50,
            "currency": "USD",
            "type": "General Admission"
        }
    ]
    
    client = ApifyTicketmasterClient(api_token="test_token")
    pricing = client.get_event_prices("https://ticketmaster.com/event")
    
    assert pricing.platform == "ticketmaster"
    assert pricing.event_id == "https://ticketmaster.com/event"
    assert len(pricing.prices) == 1
    assert pricing.prices[0].min_price == 125.50
    assert pricing.prices[0].max_price == 125.50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ticketmaster.py -v`
Expected: FAIL with "ImportError: cannot import name 'ApifyTicketmasterClient'"

- [ ] **Step 3: Write minimal implementation**

```python
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

        # Run the Actor and wait for it to finish
        run = self.client.actor(self.ACTOR_ID).call(run_input=run_input)

        # Fetch results from the dataset
        prices = []
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            price_val = float(item.get("price", 0.0))
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ticketmaster.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ticket_pricing/ticketmaster.py tests/test_ticketmaster.py
git commit -m "feat: implement apify ticketmaster client for exact pricing"
```

### Task 3: Implement Eventbrite API Client

**Files:**
- Create: `src/ticket_pricing/eventbrite.py`
- Create: `tests/test_eventbrite.py`

**Interfaces:**
- Consumes: `BaseTicketClient`, `EventPricing`, `PriceRange` from `src/ticket_pricing/models.py`
- Produces: `EventbriteClient`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_eventbrite.py
import pytest
import responses
from ticket_pricing.eventbrite import EventbriteClient

@responses.activate
def test_get_event_prices_success():
    client = EventbriteClient(api_token="test_token")
    event_id = "123456789"
    
    responses.add(
        responses.GET,
        f"https://www.eventbriteapi.com/v3/events/{event_id}/ticket_classes/",
        json={
            "ticket_classes": [
                {
                    "name": "General Admission",
                    "cost": {"value": 5000, "currency": "USD"} # Eventbrite uses minor units
                }
            ]
        },
        status=200
    )
    
    pricing = client.get_event_prices(event_id)
    assert pricing.platform == "eventbrite"
    assert pricing.event_id == event_id
    assert len(pricing.prices) == 1
    assert pricing.prices[0].min_price == 50.0
    assert pricing.prices[0].max_price == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_eventbrite.py -v`
Expected: FAIL with "ImportError: cannot import name 'EventbriteClient'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/ticket_pricing/eventbrite.py
import requests
from ticket_pricing.base import BaseTicketClient
from ticket_pricing.models import EventPricing, PriceRange

class EventbriteClient(BaseTicketClient):
    BASE_URL = "https://www.eventbriteapi.com/v3"

    def __init__(self, api_token: str):
        self.api_token = api_token

    def get_event_prices(self, event_id: str) -> EventPricing:
        url = f"{self.BASE_URL}/events/{event_id}/ticket_classes/"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        prices = []
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_eventbrite.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ticket_pricing/eventbrite.py tests/test_eventbrite.py
git commit -m "feat: implement eventbrite api client"
```

### Task 4: Create Unified Fetcher Service

**Files:**
- Create: `src/ticket_pricing/service.py`
- Create: `tests/test_service.py`

**Interfaces:**
- Consumes: `ApifyTicketmasterClient`, `EventbriteClient`
- Produces: `PricingService`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_service.py
from ticket_pricing.service import PricingService
from ticket_pricing.models import EventPricing, PriceRange

def test_pricing_service_routing(mocker):
    service = PricingService(apify_token="apify_token", eventbrite_token="eb_token")
    
    mock_tm = mocker.patch.object(service.tm_client, 'get_event_prices')
    mock_eb = mocker.patch.object(service.eb_client, 'get_event_prices')
    
    service.get_price("ticketmaster", "https://ticketmaster.com/event/123")
    mock_tm.assert_called_once_with("https://ticketmaster.com/event/123")
    mock_eb.assert_not_called()
    
    service.get_price("eventbrite", "eb_123")
    mock_eb.assert_called_once_with("eb_123")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_service.py -v`
Expected: FAIL with "ImportError: cannot import name 'PricingService'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/ticket_pricing/service.py
from ticket_pricing.models import EventPricing
from ticket_pricing.ticketmaster import ApifyTicketmasterClient
from ticket_pricing.eventbrite import EventbriteClient

class PricingService:
    def __init__(self, apify_token: str, eventbrite_token: str):
        self.tm_client = ApifyTicketmasterClient(apify_token)
        self.eb_client = EventbriteClient(eventbrite_token)
        
    def get_price(self, platform: str, event_identifier: str) -> EventPricing:
        if platform.lower() == "ticketmaster":
            return self.tm_client.get_event_prices(event_identifier)
        elif platform.lower() == "eventbrite":
            return self.eb_client.get_event_prices(event_identifier)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ticket_pricing/service.py tests/test_service.py
git commit -m "feat: implement unified pricing service"
```
