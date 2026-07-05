### Task 9: Output Formats & Notifier

**Files:**
* Modify: `notifier.py`
* Create: `tests/test_notifier.py`

**Interfaces:**
* Consumes: `events_with_analysis: list`
* Produces: Concise Discord embeds
* Produces: File output to `docs/reports/upcoming_valuation_report.md`

- [ ] **Step 1: Write test for Notifier output structure**
  
  Create `tests/test_notifier.py` with:
  ```python
  import notifier

  def test_concise_embeds():
      event = {
          "artist": "Fred again..",
          "venue": "The Anthem",
          "date": "2026-09-02T20:00:00",
          "face_value": 75.0,
          "resale_lowest": 220.0,
          "url": "https://seatgeek.com/fred-again",
          "venue_city": "Washington"
      }
      analysis = {
          "priority_score": 85.0,
          "rating": "CRITICAL",
          "roi": 149.0
      }
      # Validate report formatting logic
      report_md = notifier.generate_markdown_report([(event, analysis)])
      assert "Fred again.." in report_md
      assert "CRITICAL" in report_md
  ```

- [ ] **Step 2: Run test to verify failure**
  
  Run: `pytest tests/test_notifier.py -v`
  Expected: FAIL

- [ ] **Step 3: Modify `notifier.py` to strip guessing and produce reports**
  
  Update `notifier.py` with:
  ```python
  import os
  import requests
  import json
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
          date_str = event["date"]
          
          # Clean concise details
          price_details = f"Est. Face Value: ${event['face_value']:.2f}\n"
          if event.get("resale_lowest"):
              price_details += f"Lowest Resale: ${event['resale_lowest']:.2f}"
          else:
              price_details += "Resale Market: N/A"
              
          color = 0xE74C3C if analysis["rating"] == "CRITICAL" else 0x3498DB
          
          # Generate clean link
          sh_link = stubhub_scraper.get_stubhub_search_url(artist, event.get("venue_city", ""))
          
          event_embed = {
              "title": f"🔥 [{analysis['rating']}] {artist} @ {venue}",
              "color": color,
              "description": f"{price_details}\n[Buy Ticket]({event['url']}) | [StubHub Search]({sh_link})"
          }
          embeds.append(event_embed)
          
      payload = {"embeds": embeds}
      response = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
      return response.status_code == 204 or response.status_code == 200

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
  ```

- [ ] **Step 4: Run test to verify success**
  
  Run: `pytest tests/test_notifier.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  
  ```bash
  git add notifier.py tests/test_notifier.py
  git commit -m "feat: restrict discord notifications to concise summaries and output markdown report file"
  ```

---

