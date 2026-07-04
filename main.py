import sys
import logging
import config
import seatgeek_client
import resale_checker
import stubhub_scraper
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
    """
    Main orchestrator logic.
    """
    logger.info("Initializing EDM Ticket Tracker...")
    
    # Check config
    missing = config.validate_config()
    
    # If Discord Webhook is configured, but SeatGeek keys are missing, we can offer a Mock Run
    if "DISCORD_WEBHOOK_URL" not in missing and "SEATGEEK_CLIENT_ID" in missing:
        logger.warning("SeatGeek Client ID is missing, but Discord Webhook is set.")
        logger.info("Running in Mock/Test Mode to verify Discord Webhook configuration...")
        test_mode = True
        
    elif missing:
        logger.error(f"Cannot run tracker. Missing environment configurations in .env: {', '.join(missing)}")
        logger.info("Please fill in your API keys in the .env file in your workspace directory.")
        return False

    events_to_notify = []
    
    if test_mode:
        # Mock event details to verify webhook
        logger.info("Generating mock EDM events for test notification...")
        mock_events = [
            {
                "id": 11111,
                "title": "John Summit",
                "artist": "John Summit",
                "artist_score": 0.82,
                "date": "2026-08-15T21:00:00",
                "venue": "Echostage (Washington, DC)",
                "url": "https://seatgeek.com/john-summit-tickets",
                "resale_lowest": 125.0,
                "resale_highest": 250.0,
                "resale_average": 150.0,
                "resale_count": 42,
                "face_value": 45.0,
            },
            {
                "id": 22222,
                "title": "Fred again..",
                "artist": "Fred again..",
                "artist_score": 0.89,
                "date": "2026-09-02T20:00:00",
                "venue": "The Anthem (Washington, DC)",
                "url": "https://seatgeek.com/fred-again-tickets",
                "resale_lowest": 190.0,
                "resale_highest": 400.0,
                "resale_average": 220.0,
                "resale_count": 89,
                "face_value": 75.0,
            }
        ]
        
        for event in mock_events:
            analysis = resale_checker.evaluate_deal(event)
            event["stubhub_url"] = stubhub_scraper.get_stubhub_search_url(event["artist"], "Washington DC")
            events_to_notify.append((event, analysis))
            
        logger.info("Sending mock events to Discord...")
        notifier.send_discord_notification(events_to_notify)
        logger.info("Mock Run completed successfully! Verify your Discord channel.")
        return True

    # Real Mode Execution
    logger.info("Fetching real-time EDM events from SeatGeek...")
    events = seatgeek_client.get_upcoming_edm_events()
    
    if not events:
        logger.warning("No electronic music events found near the location.")
        # Send empty report
        notifier.send_discord_notification([])
        return True

    # Sort all events by artist score (popularity) descending to prioritize sold-out potential
    events.sort(key=lambda x: x["artist_score"], reverse=True)
    
    # Select the top 5 most popular EDM artists
    top_5_events = events[:5]
    logger.info(f"Selecting top {len(top_5_events)} most popular artists for detailed pricing analysis.")

    # Process and evaluate each of the top 5 events
    for event in top_5_events:
        # Fetch national resale average as a proxy when local resale lowest is N/A
        logger.info(f"Fetching national resale price average for: {event['artist']}")
        national_avg = seatgeek_client.get_performer_resale_average(event.get("artist_id"))
        event["resale_national_avg"] = national_avg
        
        # Evaluate deal markup
        analysis = resale_checker.evaluate_deal(event)
        
        # Append StubHub Search link
        event["stubhub_url"] = stubhub_scraper.get_stubhub_search_url(event["artist"], "Washington DC")
        
        events_to_notify.append((event, analysis))
    
    # Send notification
    success = notifier.send_discord_notification(events_to_notify)
    if success:
        logger.info("Daily ticket digest sent successfully.")
    else:
        logger.error("Failed to send daily ticket digest.")
        
    return success

if __name__ == "__main__":
    # Check if user passed '--test' flag
    is_test = len(sys.argv) > 1 and sys.argv[1] == "--test"
    run_tracker(test_mode=is_test)
