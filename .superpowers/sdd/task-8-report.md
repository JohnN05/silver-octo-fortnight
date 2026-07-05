# Task 8 Report: ETL Pipeline Orchestration & Lazy Loading

## What was implemented
- Created `etl_pipeline.py` providing the `run_daily_etl` and `bootstrap_performer_history` functions to orchestrate the ETL pipeline, meeting the specification.
- Set up caching and staleness logic where a 7-day threshold is utilized to lazy load historical performer metrics (from bootstrapping).
- Wrote integration tests in `tests/test_etl.py` to cover edge cases:
  - `test_etl_lazy_loading`: Ensures fresh database gets properly populated.
  - `test_etl_fresh_cache`: Ensures cached performers within the stale threshold are NOT redundantly bootstrapped.
  - `test_etl_stale_cache`: Ensures performers who exceed the staleness threshold get repopulated.

## What was tested & Test results
- Tested lazy loading and staleness cache edge cases in `test_etl.py`.
- Result: 3/3 passed for `test_etl.py`.
- Tested the full test suite (`pytest -v`).
- Result: 45/45 passed (100%), output is pristine.

## TDD Evidence

### RED
**Command:**
`$env:PYTHONPATH="."; pytest tests/test_etl.py -v`

**Relevant failing output:**
```
______________________ ERROR collecting tests/test_etl.py ______________________
ImportError while importing test module 'C:\Users\johnn\Desktop\gemini\edm_ticket_tracker\tests\test_etl.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_etl.py:2: in <module>
    import etl_pipeline
E   ModuleNotFoundError: No module named 'etl_pipeline'
```
**Why the failure was expected:** 
The pipeline test was looking for `etl_pipeline.py` to evaluate the mock ETL logic before the file and the internal module functions were implemented.

### GREEN
**Command:**
`$env:PYTHONPATH="."; pytest tests/test_etl.py -v`

**Relevant passing output:**
```
tests/test_etl.py::test_etl_lazy_loading PASSED                          [ 33%]
tests/test_etl.py::test_etl_fresh_cache PASSED                           [ 66%]
tests/test_etl.py::test_etl_stale_cache PASSED                           [100%]

============================== 3 passed in 0.47s ==============================
```

## Files changed
- `etl_pipeline.py` (created)
- `tests/test_etl.py` (created)

## Self-review findings
- The `database.save_performer()` automatically assigns `last_updated` using `CURRENT_TIMESTAMP`. Thus, testing the stale threshold in `test_etl.py` required a manual SQL `UPDATE` statement in the test runner to forcibly override the time and prove the staleness check worked properly.
- `orchestrator.py` already had some partial overlap. Rather than delete it (since there's a test file `test_orchestrator.py` that checks it and it may be utilized by other parts not mentioned in task 8), I focused strictly on building exactly what Task 8's brief asked for in `etl_pipeline.py`. Both files coexist and their distinct tests pass.

## Issues or concerns
- None.

## Reviewer Fixes Applied
- `etl_pipeline.py`: Fixed timezone mismatch in cache expiration by using `datetime.now(timezone.utc).replace(tzinfo=None)`.
- `etl_pipeline.py`: Added `try/except Exception as e` inside the `for event in upcoming:` loop to handle external API failures gracefully.
- `etl_pipeline.py`: Removed `test_mode` branches from `run_daily_etl` and `bootstrap_performer_history`.
- `tests/test_etl.py`: Extracted DB setup/teardown into a `pytest.fixture`.
- `tests/test_etl.py`: Mocked `seatgeek_client`, `ticketmaster_client`, `stubhub_scraper`, and `bootstrap_performer_history` using `@patch` instead of relying on `test_mode`.
- `tests/test_etl.py`: Moved all imports to the top of the file.

### Fix Test Command
`$env:PYTHONPATH="."; pytest tests/test_etl.py -v`

### Fix Test Output
```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.0.2, pluggy-1.6.0 -- C:\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\johnn\Desktop\gemini\edm_ticket_tracker
plugins: anyio-4.8.0, Faker-40.21.0, requests-mock-1.12.1
collecting ... collected 3 items

tests/test_etl.py::test_etl_lazy_loading PASSED                          [ 33%]
tests/test_etl.py::test_etl_fresh_cache PASSED                           [ 66%]
tests/test_etl.py::test_etl_stale_cache PASSED                           [100%]

============================== 3 passed in 0.25s ==============================
```


### Fixes

* \tl_pipeline.py\: Added \	est_mode=False\ default argument to un_daily_etl\ function signature to conform to the brief.
* \	ests/test_etl.py\: Extracted duplicate shared mock configurations and implementation for \mock_sg\, \mock_tm\, \mock_stubhub\, and \mock_bootstrap_impl\ into a reusable pytest fixture named \default_mocks\. Tests \	est_etl_lazy_loading\, \	est_etl_fresh_cache\, and \	est_etl_stale_cache\ have been refactored to use this fixture.

### Test Results

Command: \python -m pytest tests/test_etl.py
Output:
\============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\johnn\Desktop\gemini\edm_ticket_tracker
plugins: anyio-4.8.0, Faker-40.21.0, requests-mock-1.12.1
collected 3 items

tests\test_etl.py ...                                                    [100%]

============================== 3 passed in 0.22s ==============================
\