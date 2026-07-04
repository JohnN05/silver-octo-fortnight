import requests
import json
import logging
from datetime import datetime
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Heuristics for common DC/VA venue presale codes
VENUE_PRESALE_CODES = {
    "echostage": ["ECHO", "GLOW", "CLUBGLOW", "EDM"],
    "soundcheck": ["SOUNDCHECK", "GLOW", "CLUBGLOW"],
    "anthem": ["SUPERBEST"],
    "9:30 club": ["930CLUB"],
    "9:30": ["930CLUB"],
    "merriweather": ["WEATHER"]
}

def guess_presale_codes(venue_name):
    """
    Returns common/likely presale codes for Washington DC & VA venues
    based on local club heuristics.
    """
    name_lower = venue_name.lower()
    for key, codes in VENUE_PRESALE_CODES.items():
        if key in name_lower:
            return codes
    return []

def send_discord_notification(events_with_analysis):
    """
    Formats the events and sends them as a digest to the Discord webhook.
    """
    if not config.DISCORD_WEBHOOK_URL:
        logger.error("Discord Webhook URL is missing from configuration. Cannot send notification.")
        return False

    if not events_with_analysis:
        # Send a quiet report indicating no high value items
        payload = {
            "embeds": [
                {
                    "title": "🎵 Daily EDM Ticket Tracker Digest",
                    "description": "No new high-value EDM ticket releases or high-markup events detected in the DC/VA region today.",
                    "color": 0x95A5A6,
                    "timestamp": requests.utils.quote(requests.utils.quote("")) # placeholder
                }
            ]
        }
        # Clear out empty timestamp
        payload["embeds"][0].pop("timestamp")
        try:
            r = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            r.raise_for_status()
            logger.info("Sent empty digest notification to Discord.")
            return True
        except Exception as e:
            logger.error(f"Failed to send empty digest: {e}")
            return False

    # Group and prioritize events
    # We will build embeds for the top 8 events to stay within Discord limits
    embeds = []
    
    # Title Embed
    title_embed = {
        "title": "🔥 Daily EDM Ticket Tracker & Valuer - DC / VA Area",
        "description": "Here are the top high-demand and valuable upcoming EDM ticket opportunities near you.",
        "color": 0x9B59B6, # Purple theme
    }
    embeds.append(title_embed)

    for event, analysis in events_with_analysis[:5]:
        artist = event["artist"]
        venue = event["venue"]
        date_str = event["date"]
        
        # Format date for readability
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            formatted_date = dt.strftime("%A, %b %d at %I:%M %p")
        except Exception:
            formatted_date = date_str

        # Price comparison string
        resale_lowest = event.get("resale_lowest")
        resale_national = event.get("resale_national_avg")
        face_val = analysis["est_face_value"]
        markup = analysis["markup_percentage"]
        
        price_details = f"**Est. Face Value:** ${face_val:.2f}\n"
        if resale_lowest:
            price_details += f"**Lowest Local Resale:** ${resale_lowest:.2f} *(+{markup}% markup)*\n"
        elif resale_national:
            price_details += f"**Est. Resale (US Avg):** ${resale_national:.2f} *(+{markup}% markup - proxy)*\n"
        else:
            price_details += "**Resale Market:** N/A (No secondary listings nationwide yet)\n"

        # Guess local presale codes
        guessed_codes = guess_presale_codes(venue)
        codes_str = ", ".join([f"`{c}`" for c in guessed_codes]) if guessed_codes else "Check artist social/newsletter"

        # Create event embed
        color = 0xE74C3C if analysis["is_high_markup"] else 0x3498DB # Red for high markup, Blue otherwise
        
        event_embed = {
            "title": f"🎵 {artist} @ {venue}",
            "color": color,
            "fields": [
                {
                    "name": "📅 Date & Time",
                    "value": formatted_date,
                    "inline": True
                },
                {
                    "name": "⭐ Performer Score",
                    "value": f"{int(event['artist_score'] * 100)}%",
                    "inline": True
                },
                {
                    "name": "💰 Ticket Pricing",
                    "value": price_details,
                    "inline": False
                },
                {
                    "name": "🔑 Presale / Promo Codes",
                    "value": f"Likely codes: {codes_str}",
                    "inline": False
                },
                {
                    "name": "🔗 Ticket Links",
                    "value": f"[Buy on SeatGeek]({event['url']}) | [Check StubHub]({event['stubhub_url']})",
                    "inline": False
                }
            ]
        }
        embeds.append(event_embed)

    payload = {"embeds": embeds}
    
    try:
        response = requests.post(
            config.DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        logger.info("Successfully sent event digest to Discord!")
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord webhook: {e}")
        return False

