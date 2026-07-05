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

