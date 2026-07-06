import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Credentials
SEATGEEK_CLIENT_ID = os.getenv("SEATGEEK_CLIENT_ID")
SEATGEEK_CLIENT_SECRET = os.getenv("SEATGEEK_CLIENT_SECRET")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
STALE_THRESHOLD_DAYS = 7
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# Location Settings (Default is Gaithersburg, MD)
LATITUDE = float(os.getenv("LATITUDE", 39.1434))
LONGITUDE = float(os.getenv("LONGITUDE", -77.2014))
RADIUS = os.getenv("RADIUS", "45mi")  # Covers DC & parts of Northern Virginia

# Value Thresholds
POPULARITY_THRESHOLD = float(os.getenv("POPULARITY_THRESHOLD", 0.40))  # Performer score (0.0 to 1.0)
MARKUP_THRESHOLD = float(os.getenv("MARKUP_THRESHOLD", 1.15))          # Resale / Face value ratio

def validate_config():
    """Validates that crucial settings are provided."""
    missing = []
    if not SEATGEEK_CLIENT_ID:
        missing.append("SEATGEEK_CLIENT_ID")
    if not DISCORD_WEBHOOK_URL:
        missing.append("DISCORD_WEBHOOK_URL")
    return missing
