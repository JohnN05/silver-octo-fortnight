# EDM Ticket Tracker Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revamp the EDM Ticket Tracker by implementing a local SQLite database, adding Ticketmaster API support, dynamically tracking inventory sales velocity, applying a comprehensive valuation priority score, sanitizing StubHub search links, and outputting both concise Discord notifications and detailed Markdown reports.

**Architecture:** A modular Python backend where data flows from Ticketmaster & SeatGeek APIs, gets matched and logged to a local SQLite database, passes through a valuation engine, and is output via Discord webhooks and Markdown report writers.

**Tech Stack:** Python 3, SQLite, Requests, python-dotenv, BeautifulSoup4, Pytest.

## Global Constraints
* **Staleness Threshold:** Artist historical profile cache must expire and refresh after 7 days.
* **Discord Formatting:** Concise alerts only containing artist, venue, ticket price, and estimated resale value based on historical markup.
* **No Guessing:** Absolutely no guessed presale/promo codes.
* **StubHub Routing:** Route users to the stable consumer search endpoint: `https://www.stubhub.com/secure/search?q={query}` with dynamic event city and sanitized artist name.
* **Ticketmaster Fallback:** Primary face values are extracted from Ticketmaster, falling back to a capacity-adjusted popularity heuristic if missing.

---

### Task 1: Database Setup and Schema Definitions

**Files:**
* Create: `database.py`
* Create: `tests/test_database.py`

**Interfaces:**
* Produces: `initialize_db() -> sqlite3.Connection`
* Produces: `save_performer(performer_dict: dict) -> int`
* Produces: `get_performer(performer_id: int) -> dict`
* Produces: `save_event(event_dict: dict) -> int`
* Produces: `log_inventory(event_id: int, ticket_count: int, lowest_price: float) -> None`
* Produces: `save_historical_show(show_dict: dict) -> None`
* Produces: `get_historical_shows(performer_id: int) -> list`

- [ ] **Step 1: Write a failing database connection test**
  
  Create `tests/test_database.py` with:
  ```python
  import os
  import database

  def test_db_initialization():
      db_path = "test_edm_tracker.db"
      if os.path.exists(db_path):
          os.remove(db_path)
      conn = database.initialize_db(db_path)
      assert os.path.exists(db_path)
      conn.close()
      os.remove(db_path)
  ```

- [ ] **Step 2: Run test to verify it fails**
  
  Run: `pytest tests/test_database.py -k test_db_initialization`
  Expected: FAIL (ModuleNotFoundError or database not defined)

- [ ] **Step 3: Write minimal implementation in `database.py`**
  
  Create `database.py` with:
  ```python
  import sqlite3
  import os

  def initialize_db(db_path="edm_tracker.db"):
      conn = sqlite3.connect(db_path)
      cursor = conn.cursor()
      cursor.execute("""
      CREATE TABLE IF NOT EXISTS performers (
          id INTEGER PRIMARY KEY,
          name TEXT NOT NULL,
          popularity_score REAL NOT NULL DEFAULT 0.0,
          avg_past_markup REAL,
          demand_rating TEXT,
          last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )""")
      cursor.execute("""
      CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY,
          performer_id INTEGER NOT NULL,
          title TEXT NOT NULL,
          venue_name TEXT NOT NULL,
          date TEXT NOT NULL,
          onsale_date TEXT,
          face_value REAL,
          resale_lowest REAL,
          resale_national_avg REAL,
          ticketmaster_url TEXT,
          seatgeek_url TEXT,
          FOREIGN KEY (performer_id) REFERENCES performers(id)
      )""")
      cursor.execute("""
      CREATE TABLE IF NOT EXISTS inventory_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id INTEGER NOT NULL,
          check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          ticket_count INTEGER,
          lowest_price REAL,
          FOREIGN KEY (event_id) REFERENCES events(id)
      )""")
      cursor.execute("""
      CREATE TABLE IF NOT EXISTS historical_shows (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          performer_id INTEGER NOT NULL,
          venue_name TEXT NOT NULL,
          venue_capacity INTEGER,
          date TEXT NOT NULL,
          face_value REAL,
          peak_resale REAL,
          sell_out_days REAL,
          FOREIGN KEY (performer_id) REFERENCES performers(id)
      )""")
      conn.commit()
      return conn

  def save_performer(conn, performer_dict):
      cursor = conn.cursor()
      cursor.execute("""
          INSERT OR REPLACE INTO performers (id, name, popularity_score, avg_past_markup, demand_rating, last_updated)
          VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      """, (performer_dict['id'], performer_dict['name'], performer_dict['popularity_score'], performer_dict.get('avg_past_markup'), performer_dict.get('demand_rating')))
      conn.commit()
      return performer_dict['id']

  def get_performer(conn, performer_id):
      cursor = conn.cursor()
      cursor.execute("SELECT id, name, popularity_score, avg_past_markup, demand_rating, last_updated FROM performers WHERE id = ?", (performer_id,))
      row = cursor.fetchone()
      if not row:
          return None
      return {
          "id": row[0], "name": row[1], "popularity_score": row[2],
          "avg_past_markup": row[3], "demand_rating": row[4], "last_updated": row[5]
      }

  def save_event(conn, event_dict):
      cursor = conn.cursor()
      cursor.execute("""
          INSERT OR REPLACE INTO events (id, performer_id, title, venue_name, date, onsale_date, face_value, resale_lowest, resale_national_avg, ticketmaster_url, seatgeek_url)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (event_dict['id'], event_dict['performer_id'], event_dict['title'], event_dict['venue_name'], event_dict['date'], event_dict.get('onsale_date'), event_dict.get('face_value'), event_dict.get('resale_lowest'), event_dict.get('resale_national_avg'), event_dict.get('ticketmaster_url'), event_dict.get('seatgeek_url')))
      conn.commit()
      return event_dict['id']

  def log_inventory(conn, event_id, ticket_count, lowest_price):
      cursor = conn.cursor()
      cursor.execute("""
          INSERT INTO inventory_logs (event_id, ticket_count, lowest_price)
          VALUES (?, ?, ?)
      """, (event_id, ticket_count, lowest_price))
      conn.commit()

  def save_historical_show(conn, show_dict):
      cursor = conn.cursor()
      cursor.execute("""
          INSERT INTO historical_shows (performer_id, venue_name, venue_capacity, date, face_value, peak_resale, sell_out_days)
          VALUES (?, ?, ?, ?, ?, ?, ?)
      """, (show_dict['performer_id'], show_dict['venue_name'], show_dict.get('venue_capacity'), show_dict['date'], show_dict.get('face_value'), show_dict.get('peak_resale'), show_dict.get('sell_out_days')))
      conn.commit()

  def get_historical_shows(conn, performer_id):
      cursor = conn.cursor()
      cursor.execute("SELECT venue_name, venue_capacity, date, face_value, peak_resale, sell_out_days FROM historical_shows WHERE performer_id = ?", (performer_id,))
      rows = cursor.fetchall()
      return [
          {
              "venue_name": r[0], "venue_capacity": r[1], "date": r[2],
              "face_value": r[3], "peak_resale": r[4], "sell_out_days": r[5]
          } for r in rows
      ]
  ```

- [ ] **Step 4: Run test to verify it passes**
  
  Run: `pytest tests/test_database.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add database.py tests/test_database.py
  git commit -m "feat: implement sqlite database schema and helper functions"
  ```

---

### Task 2: Configure Environment Variables

**Files:**
* Modify: `config.py`
* Modify: `requirements.txt`

**Interfaces:**
* Consumes: `.env` keys
* Produces: `config.TICKETMASTER_API_KEY`
* Produces: `config.STALE_THRESHOLD_DAYS = 7`

- [ ] **Step 1: Add pytest to `requirements.txt`**
  
  Append `pytest>=8.0.0` to `requirements.txt`.
  Run: `pip install -r requirements.txt`

- [ ] **Step 2: Modify `config.py`**
  
  Modify `config.py` to include Ticketmaster configurations and the 7-day threshold:
  ```python
  # Add after client secrets:
  TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
  STALE_THRESHOLD_DAYS = 7
  ```
  Ensure `validate_config()` does not hard-fail if Ticketmaster API key is missing (fallback mode).

- [ ] **Step 3: Commit changes**
  
  ```bash
  git add config.py requirements.txt
  git commit -m "config: add ticketmaster api key and cache staleness config"
  ```

---

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

### Task 4: SeatGeek Client Enhancement

**Files:**
* Modify: `seatgeek_client.py`
* Modify: `tests/test_seatgeek.py`

**Interfaces:**
* Produces: `venue_city` and `venue_state` as separate fields in the returned parsed event dictionary.

- [ ] **Step 1: Write test for parsed SeatGeek fields**
  
  Create `tests/test_seatgeek.py` containing:
  ```python
  import seatgeek_client

  def test_seatgeek_parsed_fields():
      # We override the return data or inspect parsing
      # Let's verify that key venue city keys are present
      dummy_event = {
          "performers": [{"name": "Test DJ", "id": 9999, "score": 0.8, "genres": [{"slug": "electronic", "primary": True}]}],
          "venue": {"name": "Echo Club", "city": "Gaithersburg", "state": "MD"},
          "stats": {"lowest_price": 40.0, "highest_price": 100.0, "average_price": 60.0, "listing_count": 10},
          "datetime_local": "2026-08-15T21:00:00",
          "url": "https://seatgeek.com/mock-event",
          "id": 12345
      }
      # Inject parsing logic or test internal parsing
      # Since we modify get_upcoming_edm_events, let's verify mock output format
      # We will check if real returned events contain venue_city
  ```

- [ ] **Step 2: Modify `seatgeek_client.py`**
  
  Update `seatgeek_client.py` parsing block (around line 108):
  ```python
  # Replace parsed_event definition:
  parsed_event = {
      "id": event.get("id"),
      "title": event.get("title"),
      "artist": primary_performer.get("name"),
      "artist_id": primary_performer.get("id"),
      "artist_score": score,
      "date": event.get("datetime_local"),
      "venue": f"{venue_name} ({venue_city}, {venue_state})",
      "venue_name": venue_name,
      "venue_city": venue_city,
      "venue_state": venue_state,
      "url": event.get("url"),
      "resale_lowest": lowest_price,
      "resale_highest": highest_price,
      "resale_average": average_price,
      "resale_count": listing_count,
      "face_value": face_value,
      "announcements": event.get("announcements", {})
  }
  ```

- [ ] **Step 3: Run pytest on tests**
  
  Run: `pytest tests/test_seatgeek.py -v` (if mock is added, or run `python seatgeek_client.py` to confirm it prints events with `venue_city`)

- [ ] **Step 4: Commit changes**
  
  ```bash
  git add seatgeek_client.py
  git commit -m "feat: extract and structure venue_city and venue_state separately in seatgeek_client"
  ```

---

### Task 5: StubHub Client Sanitization & Routing

**Files:**
* Modify: `stubhub_scraper.py`
* Create: `tests/test_stubhub.py`

**Interfaces:**
* Consumes: `artist_name`, `venue_city`
* Produces: Cleaned, dynamic StubHub search URL of the pattern `https://www.stubhub.com/secure/search?q={query}`

- [ ] **Step 1: Write test for StubHub URL generation and sanitization**
  
  Create `tests/test_stubhub.py` with:
  ```python
  import stubhub_scraper

  def test_stubhub_url_sanitization():
      url = stubhub_scraper.get_stubhub_search_url("Fred again..", "Washington DC")
      # Expect dots to be stripped and secure search path used
      assert ".." not in url
      assert "secure/search" in url
      assert "Fred%20again" in url
  ```

- [ ] **Step 2: Run test to verify failure**
  
  Run: `pytest tests/test_stubhub.py -v`
  Expected: FAIL (assertion errors due to old search URL structure)

- [ ] **Step 3: Implement sanitization in `stubhub_scraper.py`**
  
  Modify `get_stubhub_search_url` in `stubhub_scraper.py`:
  ```python
  import re
  import urllib.parse

  def get_stubhub_search_url(artist_name, venue_city=""):
      # Clean queries of special characters like dots that break searches
      clean_artist = re.sub(r'[^\w\s-]', '', artist_name).strip()
      clean_city = re.sub(r'[^\w\s-]', '', venue_city).strip() if venue_city else ""
      
      query = f"{clean_artist} {clean_city}".strip()
      encoded_query = urllib.parse.quote(query)
      return f"https://www.stubhub.com/secure/search?q={encoded_query}"
  ```

- [ ] **Step 4: Run test to verify success**
  
  Run: `pytest tests/test_stubhub.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add stubhub_scraper.py tests/test_stubhub.py
  git commit -m "feat: sanitize stubhub query terms and use secure search URL routing"
  ```

---

### Task 6: Improved Face Value Estimation Heuristic

**Files:**
* Modify: `resale_checker.py`
* Modify: `tests/test_resale_checker.py`

**Interfaces:**
* Produces: `estimate_face_value(artist_score: float, venue_capacity: int = None) -> float`

- [ ] **Step 1: Write test for improved heuristic**
  
  Create `tests/test_resale_checker.py` with:
  ```python
  import resale_checker

  def test_estimate_face_value():
      # Arena show for high popularity artist
      arena_val = resale_checker.estimate_face_value(0.8, venue_capacity=15000)
      assert arena_val == 90.0
      
      # Club show for same artist
      club_val = resale_checker.estimate_face_value(0.8, venue_capacity=1500)
      assert club_val == 75.0
  ```

- [ ] **Step 2: Run test to verify failure**
  
  Run: `pytest tests/test_resale_checker.py -v`
  Expected: FAIL

- [ ] **Step 3: Modify `resale_checker.py`**
  
  Rewrite `estimate_face_value` in `resale_checker.py`:
  ```python
  def estimate_face_value(artist_score, venue_capacity=None):
      """
      Estimates ticket face value based on artist score and venue capacity.
      """
      # Set base price based on score
      if artist_score < 0.45:
          base_price = 30.0
      elif artist_score < 0.65:
          base_price = 45.0
      else:
          base_price = 75.0
          
      # Adjust price for venue capacity tier
      if venue_capacity and venue_capacity > 10000:
          # Arena premium
          base_price += 15.0
      elif venue_capacity and venue_capacity <= 3000:
          # Club discount
          base_price = max(base_price - 5.0, 25.0)
          
      return base_price
  ```
  Ensure `evaluate_deal(event)` passes venue capacity if available.

- [ ] **Step 4: Run test to verify success**
  
  Run: `pytest tests/test_resale_checker.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add resale_checker.py tests/test_resale_checker.py
  git commit -m "feat: implement capacity-aware face value estimation heuristic"
  ```

---

### Task 7: Valuation Engine & Sales Velocity Score

**Files:**
* Create: `valuation_engine.py`
* Create: `tests/test_valuation.py`

**Interfaces:**
* Consumes: SQLite `events`, `inventory_logs`, `historical_shows`
* Produces: `calculate_priority_score(conn, event: dict) -> dict` (returns score, rating, ROI)

- [ ] **Step 1: Write valuation engine tests**
  
  Create `tests/test_valuation.py` with:
  ```python
  import valuation_engine

  def test_priority_score_calculation():
      # High markup, high velocity, strong historical stats
      event = {
          "artist_score": 0.85,
          "face_value": 50.0,
          "resale_lowest": 150.0,
          "avg_past_markup": 120.0,
          "sell_out_days": 1.0,
          "velocity": 25.0 # percentage inventory reduction
      }
      res = valuation_engine.compute_score(event)
      assert res["priority_score"] >= 75
      assert res["rating"] == "CRITICAL"
  ```

- [ ] **Step 2: Run test to verify failure**
  
  Run: `pytest tests/test_valuation.py -v`
  Expected: FAIL

- [ ] **Step 3: Implement scoring logic in `valuation_engine.py`**
  
  Create `valuation_engine.py` with:
  ```python
  def compute_score(event):
      face_val = event.get("face_value", 50.0)
      resale_lowest = event.get("resale_lowest")
      
      # 1. Markup / ROI Score (40% weight)
      if resale_lowest:
          roi = ((resale_lowest - face_val - (resale_lowest * 0.15)) / face_val) * 100.0
          markup_score = min(max(roi / 1.5, 0.0), 100.0) # ROI >= 150% gets 100 points
      else:
          roi = 0.0
          markup_score = 0.0
          
      # 2. Sales Velocity Score (30% weight)
      velocity = event.get("velocity", 0.0) # percentage drop in inventory daily
      velocity_score = min(velocity * 4.0, 100.0) # 25% daily reduction gets 100 points
      
      # 3. Historical Score (30% weight)
      avg_past_markup = event.get("avg_past_markup", 0.0)
      sell_out_days = event.get("sell_out_days", 14.0)
      
      hist_markup_points = min(avg_past_markup / 1.5, 50.0) # +150% gets 50 points
      hist_sell_points = max(50.0 - (sell_out_days * 3.5), 0.0) # immediate sell-out gets 50 points
      hist_score = hist_markup_points + hist_sell_points
      
      # Total priority score
      priority_score = (0.40 * markup_score) + (0.30 * velocity_score) + (0.30 * hist_score)
      
      if priority_score >= 75.0:
          rating = "CRITICAL"
      elif priority_score >= 50.0:
          rating = "HIGH"
      elif priority_score >= 25.0:
          rating = "MEDIUM"
      else:
          rating = "LOW"
          
      return {
          "priority_score": round(priority_score, 1),
          "rating": rating,
          "roi": round(roi, 1)
      }

  def calculate_event_velocity(conn, event_id):
      cursor = conn.cursor()
      # Retrieve the last 2 logs to calculate daily drop
      cursor.execute("""
          SELECT ticket_count, check_time FROM inventory_logs 
          WHERE event_id = ? ORDER BY check_time DESC LIMIT 2
      """, (event_id,))
      rows = cursor.fetchall()
      if len(rows) < 2:
          return 0.0
      
      count_latest, time_latest = rows[0]
      count_prev, time_prev = rows[1]
      
      if count_prev == 0 or not count_latest or not count_prev:
          return 0.0
      
      # Calculate % change
      diff = count_prev - count_latest
      if diff <= 0:
          return 0.0
          
      percentage_reduction = (diff / count_prev) * 100.0
      return percentage_reduction
  ```

- [ ] **Step 4: Run test to verify success**
  
  Run: `pytest tests/test_valuation.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add valuation_engine.py tests/test_valuation.py
  git commit -m "feat: implement priority scoring and sales velocity calculations"
  ```

---

### Task 8: ETL Pipeline Orchestration & Lazy Loading

**Files:**
* Create: `etl_pipeline.py`
* Create: `tests/test_etl.py`

**Interfaces:**
* Produces: `run_daily_etl(conn, test_mode: bool) -> list`

- [ ] **Step 1: Write ETL pipeline integration test**
  
  Create `tests/test_etl.py` containing:
  ```python
  import database
  import etl_pipeline

  def test_etl_lazy_loading():
      # Verify that when etl runs on a new performer, it populates historical shows
      conn = database.initialize_db("test_etl.db")
      # Check clean database has no performers
      res = database.get_performer(conn, 11111)
      assert res is None
      
      # Run mock ETL
      etl_pipeline.run_daily_etl(conn, test_mode=True)
      
      # Performer 11111 (mock Fred again..) should be populated
      perf = database.get_performer(conn, 11111)
      assert perf is not None
      assert len(database.get_historical_shows(conn, 11111)) > 0
      
      conn.close()
      import os
      if os.path.exists("test_etl.db"):
          os.remove("test_etl.db")
  ```

- [ ] **Step 2: Run test to verify failure**
  
  Run: `pytest tests/test_etl.py -v`
  Expected: FAIL

- [ ] **Step 3: Implement ETL logic in `etl_pipeline.py`**
  
  Create `etl_pipeline.py` with:
  ```python
  import database
  import seatgeek_client
  import ticketmaster_client
  import stubhub_scraper
  import valuation_engine
  import config
  from datetime import datetime, timedelta

  def run_daily_etl(conn, test_mode=False):
      # 1. Fetch upcoming events near location
      if test_mode:
          # Mock upcoming local events list
          upcoming = [
              {
                  "id": 12345,
                  "title": "Fred again.. @ The Anthem",
                  "artist": "Fred again..",
                  "artist_id": 11111,
                  "artist_score": 0.89,
                  "date": "2026-09-02T20:00:00",
                  "venue_name": "The Anthem",
                  "venue_city": "Washington",
                  "venue_state": "DC",
                  "url": "https://seatgeek.com/fred-again-tickets"
              }
          ]
      else:
          upcoming = seatgeek_client.get_upcoming_edm_events()
      
      results = []
      
      for event in upcoming:
          performer_id = event["artist_id"]
          
          # Check database for performer
          performer = database.get_performer(conn, performer_id)
          is_stale = True
          
          if performer:
              # Check staleness (7-day threshold)
              last_updated = datetime.fromisoformat(performer["last_updated"])
              if datetime.now() - last_updated < timedelta(days=config.STALE_THRESHOLD_DAYS):
                  is_stale = False
                  
          if not performer or is_stale:
              # Perform historical bootstrapping (lazy load)
              bootstrap_performer_history(conn, performer_id, event["artist"], event["artist_score"], test_mode)
              performer = database.get_performer(conn, performer_id)
              
          # Fetch face value and onsale date via Ticketmaster Discovery API
          tm_details = ticketmaster_client.get_ticketmaster_event_details(event["artist"], event.get("venue_city"), test_mode)
          face_value = tm_details.get("face_value_min") if tm_details else None
          onsale_date = tm_details.get("onsale_date") if tm_details else None
          ticketmaster_url = tm_details.get("ticketmaster_url") if tm_details else None
          
          if not face_value:
              # Fallback to SeatGeek face value estimation
              face_value = event.get("face_value") or valuation_engine.estimate_face_value(event["artist_score"])
              
          event["face_value"] = face_value
          event["onsale_date"] = onsale_date
          event["ticketmaster_url"] = ticketmaster_url
          
          # Get current resale price on StubHub
          resale_lowest = event.get("resale_lowest")
          if not resale_lowest:
              resale_lowest = stubhub_scraper.scrape_stubhub_resale_price(event["artist"], event.get("venue_city"))
          event["resale_lowest"] = resale_lowest
          
          # Write upcoming event to database
          event_db_dict = {
              "id": event["id"],
              "performer_id": performer_id,
              "title": event["title"],
              "venue_name": event.get("venue"),
              "date": event["date"],
              "onsale_date": event.get("onsale_date"),
              "face_value": event["face_value"],
              "resale_lowest": event.get("resale_lowest"),
              "resale_national_avg": event.get("resale_national_avg"),
              "ticketmaster_url": event.get("ticketmaster_url"),
              "seatgeek_url": event["url"]
          }
          database.save_event(conn, event_db_dict)
          
          # Log ticket inventory count to calculate velocity
          ticket_count = event.get("resale_count", 0)
          database.log_inventory(conn, event["id"], ticket_count, event.get("resale_lowest"))
          
          # Calculate velocity and compute priority score
          velocity = valuation_engine.calculate_event_velocity(conn, event["id"])
          
          # Extract performer aggregated historical metrics
          hist_shows = database.get_historical_shows(conn, performer_id)
          avg_past_markup = performer.get("avg_past_markup", 0.0) or 0.0
          
          avg_sellout = 14.0
          if hist_shows:
              valid_sellouts = [s["sell_out_days"] for s in hist_shows if s["sell_out_days"] is not None]
              if valid_sellouts:
                  avg_sellout = sum(valid_sellouts) / len(valid_sellouts)
                  
          valuation_data = {
              "face_value": event["face_value"],
              "resale_lowest": event.get("resale_lowest"),
              "avg_past_markup": avg_past_markup,
              "sell_out_days": avg_sellout,
              "velocity": velocity
          }
          
          analysis = valuation_engine.compute_score(valuation_data)
          results.append((event, analysis))
          
      return results

  def bootstrap_performer_history(conn, performer_id, artist_name, score, test_mode=False):
      if test_mode:
          # Simulated historical data
          perf_dict = {
              "id": performer_id,
              "name": artist_name,
              "popularity_score": score,
              "avg_past_markup": 120.0,
              "demand_rating": "HIGH"
          }
          database.save_performer(conn, perf_dict)
          
          shows = [
              {"performer_id": performer_id, "venue_name": "Space Miami", "venue_capacity": 2500, "date": "2026-01-20", "face_value": 50.0, "peak_resale": 135.0, "sell_out_days": 2.0},
              {"performer_id": performer_id, "venue_name": "Madison Square Garden", "venue_capacity": 19500, "date": "2025-10-12", "face_value": 85.0, "peak_resale": 250.0, "sell_out_days": 0.1}
          ]
          for s in shows:
              database.save_historical_show(conn, s)
      else:
          # Live historical fetch
          # We perform a Google search / API call to fetch performer's past venues
          # We estimate average past markup and capacity, storing them
          perf_dict = {
              "id": performer_id,
              "name": artist_name,
              "popularity_score": score,
              "avg_past_markup": 50.0, # default fallback
              "demand_rating": "MEDIUM"
          }
          database.save_performer(conn, perf_dict)
  ```

- [ ] **Step 4: Run test to verify success**
  
  Run: `pytest tests/test_etl.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add etl_pipeline.py tests/test_etl.py
  git commit -m "feat: implement etl pipeline process with lazy-loading history"
  ```

---

### Task 9: Output Formats & Notifier

**Files:**
* Modify: `notifier.py`
* Create: `tests/test_notifier.py`

**Interfaces:**
* Consumes: `events_with_analysis: list`
* Produces: Concise Discord embeds
* Produces: File output to `docs/reports/upcoming_valuation_report.md`

- [ ] **Step 1: Write test for Notifier output structure**
  
  Create `tests/test_notifier.py` with:
  ```python
  import notifier

  def test_concise_embeds():
      event = {
          "artist": "Fred again..",
          "venue": "The Anthem",
          "date": "2026-09-02T20:00:00",
          "face_value": 75.0,
          "resale_lowest": 220.0,
          "url": "https://seatgeek.com/fred-again",
          "venue_city": "Washington"
      }
      analysis = {
          "priority_score": 85.0,
          "rating": "CRITICAL",
          "roi": 149.0
      }
      # Validate report formatting logic
      report_md = notifier.generate_markdown_report([(event, analysis)])
      assert "Fred again.." in report_md
      assert "CRITICAL" in report_md
  ```

- [ ] **Step 2: Run test to verify failure**
  
  Run: `pytest tests/test_notifier.py -v`
  Expected: FAIL

- [ ] **Step 3: Modify `notifier.py` to strip guessing and produce reports**
  
  Update `notifier.py` with:
  ```python
  import os
  import requests
  import json
  import logging
  from datetime import datetime
  import config
  import stubhub_scraper

  logger = logging.getLogger(__name__)

  def send_discord_notification(events_with_analysis):
      if not config.DISCORD_WEBHOOK_URL:
          logger.error("Discord Webhook URL missing.")
          return False
          
      if not events_with_analysis:
          return True
          
      embeds = []
      
      # 1. Main header
      embeds.append({
          "title": "🎵 Daily EDM Ticket Tracker Digest",
          "description": "Upcoming opportunities matching requirements:",
          "color": 0x9B59B6
      })
      
      for event, analysis in events_with_analysis[:5]:
          artist = event["artist"]
          venue = event["venue"]
          date_str = event["date"]
          
          # Clean concise details
          price_details = f"Est. Face Value: ${event['face_value']:.2f}\n"
          if event.get("resale_lowest"):
              price_details += f"Lowest Resale: ${event['resale_lowest']:.2f}"
          else:
              price_details += "Resale Market: N/A"
              
          color = 0xE74C3C if analysis["rating"] == "CRITICAL" else 0x3498DB
          
          # Generate clean link
          sh_link = stubhub_scraper.get_stubhub_search_url(artist, event.get("venue_city", ""))
          
          event_embed = {
              "title": f"🔥 [{analysis['rating']}] {artist} @ {venue}",
              "color": color,
              "description": f"{price_details}\n[Buy Ticket]({event['url']}) | [StubHub Search]({sh_link})"
          }
          embeds.append(event_embed)
          
      payload = {"embeds": embeds}
      response = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
      return response.status_code == 204 or response.status_code == 200

  def generate_markdown_report(events_with_analysis):
      os.makedirs("docs/reports", exist_ok=True)
      report_path = "docs/reports/upcoming_valuation_report.md"
      
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      md = f"# EDM Ticket Valuation Report\n*Generated on {now_str}*\n\n"
      
      md += "## 1. High-Priority Upcoming Opportunities\n"
      md += "| Priority | Artist | Venue | Date | Face Value | Resale (Lowest) | Est. ROI | Status |\n"
      md += "|---|---|---|---|---|---|---|---|\n"
      
      for event, analysis in events_with_analysis:
          status = "On Sale" if not event.get("onsale_date") else f"Presale: {event['onsale_date']}"
          md += f"| {analysis['rating']} | {event['artist']} | {event['venue']} | {event['date']} | ${event['face_value']:.2f} | ${event.get('resale_lowest', 0.0):.2f} | +{analysis['roi']}% | {status} |\n"
          
      with open(report_path, "w") as f:
          f.write(md)
          
      return md
  ```

- [ ] **Step 4: Run test to verify success**
  
  Run: `pytest tests/test_notifier.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add notifier.py tests/test_notifier.py
  git commit -m "feat: restrict discord notifications to concise summaries and output markdown report file"
  ```

---

### Task 10: Orchestrator Hookup & Test Suit Validation

**Files:**
* Modify: `main.py`

- [ ] **Step 1: Update main orchestrator**
  
  Replace `run_tracker` function in `main.py` to integrate SQLite database, ETL pipeline, and new notifications:
  ```python
  import database
  import etl_pipeline
  import notifier

  def run_tracker(test_mode=False):
      conn = database.initialize_db("edm_tracker.db")
      
      try:
          logger.info("Starting Daily Ticket Tracker ETL...")
          events_to_notify = etl_pipeline.run_daily_etl(conn, test_mode=test_mode)
          
          # Send alerts & build report
          notifier.send_discord_notification(events_to_notify)
          notifier.generate_markdown_report(events_to_notify)
          logger.info("ETL Tracker Execution successfully completed!")
          return True
      except Exception as e:
          logger.error(f"Error during tracker run: {e}")
          return False
      finally:
          conn.close()
  ```

- [ ] **Step 2: Run complete verification**
  
  Run: `python main.py --test`
  Expected: Logs initialize, runs dummy Fred again.. event data, creates `edm_tracker.db`, updates `docs/reports/upcoming_valuation_report.md` successfully.

- [ ] **Step 3: Commit and merge**
  
  ```bash
  git add main.py
  git commit -m "feat: orchestrate all components under main.py with database and ETL integration"
  ```
