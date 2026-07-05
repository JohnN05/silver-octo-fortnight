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

