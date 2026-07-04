# Task 1 Report: Database Setup and Schema Definitions

## What was implemented
Implemented the foundational SQLite database schema and helper functions as specified in the task brief. Created the `database.py` module with functions for initialization and CRUD operations.

## Testing and TDD Evidence
Followed TDD as requested. 

**RED (Failing Test):**
Command: `pytest tests/test_database.py -k test_db_initialization`
Output snippet:
```
E   ModuleNotFoundError: No module named 'database'
```
Why failure was expected: The test tried to import `database.py` before it was created.

**GREEN (Passing Test):**
Command: `$env:PYTHONPATH="."; pytest tests/test_database.py -v`
Output snippet:
```
tests/test_database.py::test_db_initialization PASSED                    [100%]
============================== 1 passed in 0.56s ==============================
```
Why passing: The `database.py` module was implemented with the required `initialize_db` function and schemas.

## Files changed
- `tests/test_database.py` (Created)
- `database.py` (Created)

## Self-review findings
- The schema precisely matches the requirements (tables for performers, events, inventory_logs, and historical_shows).
- The functions perform the requested database inserts, updates, and queries.
- TDD steps were correctly followed. 

## Issues or concerns
- Needed to explicitly set `$env:PYTHONPATH="."` for `pytest` to locate `database.py` during the test run in this environment. No other concerns.

### Fixes Applied (database.py)
1. **Foreign Key Enforcement**: Added `cursor.execute("PRAGMA foreign_keys = ON")` in `initialize_db`.
2. **Error Handling**: Wrapped all operations (`save_performer`, `get_performer`, `save_event`, `log_inventory`, `save_historical_show`, `get_historical_shows`, and `initialize_db`) in `try...except sqlite3.Error` blocks. Added logging and raised a custom `DatabaseError`.
3. **Comprehensive Tests**: Added comprehensive CRUD tests and foreign key constraint tests in `tests/test_database.py`.

### Test Execution
Command: `python -m pytest tests/test_database.py -v`

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.0.2, pluggy-1.6.0 -- C:\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\johnn\Desktop\gemini\edm_ticket_tracker
plugins: anyio-4.8.0, Faker-40.21.0, requests-mock-1.12.1
collecting ... collected 8 items

tests/test_database.py::test_db_initialization PASSED                    [ 12%]
tests/test_database.py::test_save_and_get_performer PASSED               [ 25%]
tests/test_database.py::test_get_performer_not_found PASSED              [ 37%]
tests/test_database.py::test_save_event_foreign_key_error PASSED         [ 50%]
tests/test_database.py::test_save_event_and_log_inventory PASSED         [ 62%]
tests/test_database.py::test_log_inventory_foreign_key_error PASSED      [ 75%]
tests/test_database.py::test_historical_shows PASSED                     [ 87%]
tests/test_database.py::test_save_historical_show_foreign_key_error PASSED [100%]

============================== 8 passed in 0.28s ==============================
```
