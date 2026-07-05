### Task 3: Ticketmaster API Client Integration

**Files:**
* Create: `ticketmaster_client.py`
* Create: `tests/test_ticketmaster.py`

**Interfaces:**
* Produces: `get_ticketmaster_event_details(artist_name: str, venue_city: str) -> dict`
* Produces: `mock_ticketmaster_event_details(artist_name: str) -> dict`

- [ ] **Step 1: Write test for Ticketmaster client (supporting Mock/Real mode)**
  
  Create `tests/test_ticketmaster.py` with:
  ```python
  import ticketmaster_client
  import config

  def test_mock_ticketmaster_details():
      details = ticketmaster_client.get_ticketmaster_event_details("Fred again..", "Washington", test_mode=True)
      assert details is not None
      assert details["face_value_min"] == 75.0
      assert details["face_value_max"] == 95.0
      assert details["onsale_date"] == "2026-07-15T10:00:00"
  ```

- [ ] **Step 2: Run test to verify it fails**
  
  Run: `pytest tests/test_ticketmaster.py -v`
  Expected: FAIL (ModuleNotFoundError or function not defined)

- [ ] **Step 3: Implement client in `ticketmaster_client.py`**
  
  Create `ticketmaster_client.py` with:
  ```python
  import requests
  import logging
  import config

  logger = logging.getLogger(__name__)

  def mock_ticketmaster_event_details(artist_name):
      if "Fred again" in artist_name:
          return {
              "face_value_min": 75.0,
              "face_value_max": 95.0,
              "onsale_date": "2026-07-15T10:00:00",
              "ticketmaster_url": "https://www.ticketmaster.com/mock-fred-again"
          }
      elif "John Summit" in artist_name:
          return {
              "face_value_min": 45.0,
              "face_value_max": 65.0,
              "onsale_date": "2026-07-10T12:00:00",
              "ticketmaster_url": "https://www.ticketmaster.com/mock-john-summit"
          }
      return None

  def get_ticketmaster_event_details(artist_name, venue_city, test_mode=False):
      if test_mode or not config.TICKETMASTER_API_KEY:
          return mock_ticketmaster_event_details(artist_name)
      
      url = "https://app.ticketmaster.com/discovery/v2/events.json"
      params = {
          "apikey": config.TICKETMASTER_API_KEY,
          "keyword": artist_name,
          "city": venue_city,
          "classificationName": "dance",
          "size": 1
      }
      try:
          response = requests.get(url, params=params, timeout=10)
          response.raise_for_status()
          data = response.json()
          events = data.get("_embedded", {}).get("events", [])
          if not events:
              return None
          
          event = events[0]
          price_ranges = event.get("priceRanges", [])
          face_min = price_ranges[0].get("min") if price_ranges else None
          face_max = price_ranges[0].get("max") if price_ranges else None
          
          onsales = event.get("sales", {}).get("public", {})
          onsale_date = onsales.get("startDateTime")
          
          return {
              "face_value_min": face_min,
              "face_value_max": face_max,
              "onsale_date": onsale_date,
              "ticketmaster_url": event.get("url")
          }
      except Exception as e:
          logger.error(f"Error querying Ticketmaster for {artist_name}: {e}")
          return None
  ```

- [ ] **Step 4: Run test to verify it passes**
  
  Run: `pytest tests/test_ticketmaster.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add ticketmaster_client.py tests/test_ticketmaster.py
  git commit -m "feat: implement ticketmaster client with API lookup and mock mode"
  ```

---

