import sys
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


if __name__ == "__main__":
    # Check if user passed '--test' flag
    is_test = len(sys.argv) > 1 and sys.argv[1] == "--test"
    run_tracker(test_mode=is_test)
