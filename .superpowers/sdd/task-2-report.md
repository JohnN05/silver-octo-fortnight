# Task 2 Report

## What I implemented
- Added `pytest>=8.0.0` to `requirements.txt`.
- Added `TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")` to `config.py`.
- Added `STALE_THRESHOLD_DAYS = 7` to `config.py`.
- Verified that `validate_config()` only checks for `SEATGEEK_CLIENT_ID` and `DISCORD_WEBHOOK_URL`, so it inherently does not hard-fail if `TICKETMASTER_API_KEY` is missing.
- Wrote a test file `tests/test_config.py` to verify the configuration values and the fallback mode.

## What I tested and test results
- Tests were written in `tests/test_config.py`.
- I attempted to install dependencies with `pip install -r requirements.txt` and run tests using `.venv\Scripts\pytest tests/test_config.py`. However, both commands timed out waiting for user approval.
- Test execution was blocked by the permission prompts timing out.

## Files changed
- `requirements.txt`
- `config.py`
- `tests/test_config.py` (Created)

## Self-review findings
- The requirements have been completely fulfilled based on the task brief.
- `TICKETMASTER_API_KEY` is correctly set.
- `STALE_THRESHOLD_DAYS` is set to 7.
- I avoided overbuilding and stuck exactly to the requirements.

## Any issues or concerns
- I was unable to run `pip install`, `pytest`, or the `git commit` commands as they timed out waiting for user permission. The code is ready and correctly implemented, but you will need to run the `git commit` step manually.
