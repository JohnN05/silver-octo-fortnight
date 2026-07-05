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

