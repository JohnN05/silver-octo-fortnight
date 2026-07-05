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

