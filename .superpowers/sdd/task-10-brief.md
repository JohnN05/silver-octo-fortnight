### Task 10: Orchestrator Hookup & Test Suit Validation

**Files:**
* Modify: `main.py`

- [ ] **Step 1: Update main orchestrator**
  
  Replace `run_tracker` function in `main.py` to integrate SQLite database, ETL pipeline, and new notifications:
  ```python
  import database
  import etl_pipeline
  import notifier

  def run_tracker(test_mode=False):
      conn = database.initialize_db("edm_tracker.db")
      
      try:
          logger.info("Starting Daily Ticket Tracker ETL...")
          events_to_notify = etl_pipeline.run_daily_etl(conn, test_mode=test_mode)
          
          # Send alerts & build report
          notifier.send_discord_notification(events_to_notify)
          notifier.generate_markdown_report(events_to_notify)
          logger.info("ETL Tracker Execution successfully completed!")
          return True
      except Exception as e:
          logger.error(f"Error during tracker run: {e}")
          return False
      finally:
          conn.close()
  ```

- [ ] **Step 2: Run complete verification**
  
  Run: `python main.py --test`
  Expected: Logs initialize, runs dummy Fred again.. event data, creates `edm_tracker.db`, updates `docs/reports/upcoming_valuation_report.md` successfully.

- [ ] **Step 3: Commit and merge**
  
  ```bash
  git add main.py
  git commit -m "feat: orchestrate all components under main.py with database and ETL integration"
  ```
