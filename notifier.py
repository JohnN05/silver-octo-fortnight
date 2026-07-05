import os
import json
import requests
import logging
from datetime import datetime
import config
import stubhub_scraper

logger = logging.getLogger(__name__)

def send_discord_notification(events_with_analysis):
    if not config.DISCORD_WEBHOOK_URL:
        logger.error("Discord Webhook URL missing.")
        return False
        
    if not events_with_analysis:
        return True
        
    embeds = []
    
    # 1. Main header
    embeds.append({
        "title": "🎵 Daily EDM Ticket Tracker Digest",
        "description": "Upcoming opportunities matching requirements:",
        "color": 0x9B59B6
    })
    
    for event, analysis in events_with_analysis[:5]:
        artist = event["artist"]
        venue = event["venue"]
        
        # Clean concise details
        price_details = f"Est. Face Value: ${event['face_value']:.2f}\n"
        est_resale = event['face_value'] * (1 + event.get('avg_past_markup', 0))
        price_details += f"Estimated Resale Value: ${est_resale:.2f}"
            
        color = 0xE74C3C if analysis["rating"] == "CRITICAL" else 0x3498DB
        
        # Generate clean link
        sh_link = stubhub_scraper.get_stubhub_search_url(artist, event.get("venue_city", ""))
        
        event_embed = {
            "title": f"🔥 [{analysis['rating']}] {artist} @ {venue}",
            "color": color,
            "description": f"{price_details}\n[Buy Ticket]({event['url']}) | [StubHub Search]({sh_link})"
        }
        embeds.append(event_embed)
        
    # Add a final embed linking to the dashboard
    dashboard_url = "https://JohnN05.github.io/silver-octo-fortnight/"
    embeds.append({
        "title": "📊 View Full Pricing Dashboard",
        "url": dashboard_url,
        "description": "Click here to view interactive charts, analysis, and more details on any device.",
        "color": 0x2C3E50
    })
        
    payload = {"embeds": embeds}
    try:
        response = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 204 or response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error sending Discord notification: {e}")
        return False

def generate_markdown_report(events_with_analysis):
    os.makedirs("docs/reports", exist_ok=True)
    report_path = "docs/reports/upcoming_valuation_report.md"
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = f"# EDM Ticket Valuation Report\n*Generated on {now_str}*\n\n"
    
    md += "## 1. High-Priority Upcoming Opportunities\n"
    md += "| Priority | Artist | Venue | Date | Face Value | Resale (Lowest) | Est. ROI | Status |\n"
    md += "|---|---|---|---|---|---|---|---|\n"
    
    for event, analysis in events_with_analysis:
        status = "On Sale" if not event.get("onsale_date") else f"Presale: {event['onsale_date']}"
        md += f"| {analysis['rating']} | {event['artist']} | {event['venue']} | {event['date']} | ${event['face_value']:.2f} | ${event.get('resale_lowest', 0.0):.2f} | +{analysis['roi']}% | {status} |\n"
        
    with open(report_path, "w") as f:
        f.write(md)
        
    return md

def generate_json_data(events_with_analysis):
    os.makedirs("docs", exist_ok=True)
    json_path = "docs/data.json"
    
    data = []
    for event, analysis in events_with_analysis:
        event_copy = event.copy()
        event_copy["analysis_rating"] = analysis["rating"]
        event_copy["analysis_roi"] = analysis["roi"]
        
        # Calculate estimated resale
        est_resale = event['face_value'] * (1 + event.get('avg_past_markup', 0))
        event_copy["estimated_resale"] = est_resale
        
        data.append(event_copy)
        
    with open(json_path, "w") as f:
        json.dump({"last_updated": datetime.now().isoformat(), "events": data}, f, indent=4)
        
    logger.info(f"Exported {len(data)} events to {json_path}")
    return json_path
