# Task 5 Report

## What was implemented
- Updated `get_stubhub_search_url` in `stubhub_scraper.py` to sanitize `artist_name` and `venue_city` by removing special characters like dots using regex.
- Updated the URL path to use `secure/search` instead of `find/s/`.
- Created `tests/test_stubhub.py` with URL sanitization test, as well as comprehensive mocked tests for `scrape_stubhub_resale_price` covering both happy paths (INITIAL_STATE JSON and HTML text fallback) and error paths (403, non-200, exceptions).

## What was tested and test results
- `test_stubhub_url_sanitization`: Verifies characters like dots are stripped and correct secure URL path is generated.
- `test_scrape_stubhub_resale_price_initial_state`: Verifies parsing price from JSON blob.
- `test_scrape_stubhub_resale_price_regex`: Verifies parsing price from fallback text.
- `test_scrape_stubhub_resale_price_403`: Verifies returning `None` gracefully on 403.
- `test_scrape_stubhub_resale_price_non_200`: Verifies returning `None` gracefully on 500 error.
- `test_scrape_stubhub_resale_price_exception`: Verifies returning `None` gracefully on ConnectTimeout.
- All 27 tests in the full suite passed successfully.

## TDD Evidence

### RED
**Command:** `python -m pytest tests/test_stubhub.py -v` (Initial run after writing test)
**Failing Output:**
```
================================== FAILURES ===================================
________________________ test_stubhub_url_sanitization ________________________

    def test_stubhub_url_sanitization():
        url = stubhub_scraper.get_stubhub_search_url("Fred again..", "Washington DC")
        # Expect dots to be stripped and secure search path used
>       assert ".." not in url
E       AssertionError: assert '..' not in 'https://www...hington%20DC'
E         
E         '..' is contained here:
E           https://www.stubhub.com/find/s/?q=Fred%20again..%20Washington%20DC
E         ?                                               ++
```
**Why the failure was expected:** The URL generation function previously did not sanitize inputs, so ".." remained. It also didn't use `secure/search`.

### GREEN
**Command:** `python -m pytest tests/test_stubhub.py -v` (Run after implementing fix and additional tests)
**Passing Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.0.2, pluggy-1.6.0 -- C:\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\johnn\Desktop\gemini\edm_ticket_tracker
plugins: anyio-4.8.0, Faker-40.21.0, requests-mock-1.12.1
collecting ... collected 6 items

tests/test_stubhub.py::test_stubhub_url_sanitization PASSED              [ 16%]
tests/test_stubhub.py::test_scrape_stubhub_resale_price_initial_state PASSED [ 33%]
tests/test_stubhub.py::test_scrape_stubhub_resale_price_regex PASSED     [ 50%]
tests/test_stubhub.py::test_scrape_stubhub_resale_price_403 PASSED       [ 66%]
tests/test_stubhub.py::test_scrape_stubhub_resale_price_non_200 PASSED   [ 83%]
tests/test_stubhub.py::test_scrape_stubhub_resale_price_exception PASSED [100%]

============================== 6 passed in 0.16s ==============================
```

## Files changed
- `stubhub_scraper.py`
- `tests/test_stubhub.py` (created)

## Self-review findings
- Code adheres to the task specifications exactly.
- Both happy and error paths are thoroughly tested using `requests_mock`.
- Commits reflect the exact task details cleanly.

## Issues or concerns
- None.
