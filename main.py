import sys
import subprocess
import logging
import database
import etl_pipeline
import notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_tracker():
    conn = database.initialize_db("edm_tracker.db")
    
    try:
        logger.info("Starting Daily Ticket Tracker ETL...")
        events_to_notify = etl_pipeline.run_daily_etl(conn)
        
        # Send alerts & build report
        notifier.send_discord_notification(events_to_notify)
        notifier.generate_markdown_report(events_to_notify)
        notifier.generate_json_data(events_to_notify)
        
        # Auto-commit and push the data update (only if data.json changed)
        try:
            subprocess.run(["git", "add", "docs/data.json"], check=True)
            diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"])
            if diff_result.returncode != 0:
                subprocess.run(["git", "commit", "-m", "chore: update dashboard data [skip ci]"], check=True)
                subprocess.run(["git", "push", "origin", "main"], check=True)
                logger.info("Successfully pushed updated data.json to GitHub")
            else:
                logger.info("No changes to data.json — skipping commit and push")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git push failed: {e}")

        logger.info("ETL Tracker Execution successfully completed!")
        return True
    except Exception as e:
        logger.error(f"Error during tracker run: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # Check if user passed '--test' flag
    is_test = len(sys.argv) > 1 and sys.argv[1] == "--test"
    if is_test:
        from unittest.mock import patch
        
        test_events = [
            {
                "id": 22222,
                "title": "Fred again..",
                "artist": "Fred again..",
                "artist_id": 99999,
                "artist_score": 0.89,
                "date": "2026-09-02T20:00:00",
                "venue": "The Anthem (Washington, DC)",
                "venue_name": "The Anthem",
                "venue_city": "Washington",
                "venue_state": "DC",
                "url": "https://seatgeek.com/fred-again-tickets",
                "resale_lowest": 190.0,
                "resale_highest": 400.0,
                "resale_average": 220.0,
                "resale_count": 89,
                "face_value": 75.0,
                "venue_capacity": 6000,
            }
        ]
        
        with patch("seatgeek_client.get_upcoming_edm_events", return_value=test_events):
            run_tracker()
    else:
        run_tracker()
