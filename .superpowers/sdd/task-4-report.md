# Task 4 Report

## Implementation Details
- Created `tests/test_seatgeek.py` with tests for the parsed fields, success cases, request exception, value error, and the resale average functions, following TDD.
- Used `@patch` to mock `requests.get` and isolate API calls for deterministic testing, and safely mocked `config` variables like `config.SEATGEEK_CLIENT_ID` to avoid state leaks.
- Modified `seatgeek_client.py` to extract `venue_city` and `venue_state` and include them separately along with `venue_name` in the returned parsed event dictionary.
- Added type hints (e.g., `List[Dict[str, Any]]`) to function definitions in `seatgeek_client.py`.
- Improved error handling in `seatgeek_client.py` to catch `ValueError` (for invalid JSON decoding) in addition to `requests.exceptions.RequestException`.
- Made `.get()` usages safer by providing empty dict/list fallbacks (e.g., `event.get("stats") or {}`) to prevent `AttributeError` if the key exists but is explicitly `None`.
- Fixed Python 3.12 `datetime.utcnow()` deprecation warning by replacing it with `datetime.now(timezone.utc)`.

## Test Results
**TDD Evidence**:
- **RED Phase**:
  Command run: `python -m pytest tests/test_seatgeek.py -v`
  Output excerpt:
  ```
  E               KeyError: 'venue_name'
  tests\test_seatgeek.py:34: KeyError
  ...
  E               ValueError: Invalid JSON
  ```
  Why expected: `seatgeek_client.py` was not yet updated to populate `venue_name`, `venue_city`, and `venue_state`, nor did it handle the injected `ValueError` appropriately.
- **GREEN Phase**:
  Command run: `python -m pytest tests/test_seatgeek.py -v`
  Output excerpt:
  ```
  tests/test_seatgeek.py::test_seatgeek_parsed_fields PASSED               [ 14%]
  tests/test_seatgeek.py::test_get_upcoming_edm_events_success PASSED      [ 28%]
  tests/test_seatgeek.py::test_get_upcoming_edm_events_request_exception PASSED [ 42%]
  tests/test_seatgeek.py::test_get_upcoming_edm_events_value_error PASSED  [ 57%]
  ...
  ============================== 7 passed in 0.10s ==============================
  ```
- **Full Test Suite**: `python -m pytest -v` -> 21 passed in 0.24s.

## Files Changed
- `tests/test_seatgeek.py` (Created)
- `seatgeek_client.py` (Modified)

## Self-Review Findings
- **Completeness**: All requirements from the brief were met, including the detailed checklist for handling errors and using safe `.get()` methods.
- **Quality**: Type hints were added to `seatgeek_client.py`. Functions handle errors properly and log them instead of crashing. Tests verify behavior by checking parsed return values.
- **Discipline**: Followed TDD effectively, keeping changes focused on the SeatGeek client and its direct requirements without scope creep.
