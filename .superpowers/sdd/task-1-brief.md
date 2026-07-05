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

