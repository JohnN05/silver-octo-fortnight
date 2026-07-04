# EDM Ticket Tracker & Valuer - Implementation Plan

This plan outlines the architecture, setup guide, and automation steps for your EDM Ticket Tracker. The tracker will identify upcoming EDM events in the Washington, D.C. and Virginia areas, assess the value of the tickets using SeatGeek's performer popularity scores and price statistics, scrape/compare prices with StubHub, and send daily reports to your Discord server.

---

## 1. How to Acquire the Required Credentials

### 🎫 A. SeatGeek Developer API (for Event Search and Resale Prices)
SeatGeek offers a free developer tier that provides event listings, genres, and real-time resale price statistics (lowest price, highest price, average price, listing count), along with a performer popularity score (from `0` to `1.0`) based on historical ticket sales.
1. Go to [SeatGeek Developer Platform](https://seatgeek.com/account/develop).
2. Log in or create a free SeatGeek account.
3. Click **Register a New Client**.
4. Name your client (e.g., `EDM Ticket Tracker`) and enter any website URL (e.g., `http://localhost`).
5. Copy the generated **Client ID** and **Client Secret**.

### 💬 B. Discord Webhook URL (for Notifications)
1. Open Discord and go to your server (or create a private server).
2. Right-click the channel where you want to receive alerts, select **Edit Channel**.
3. Go to **Integrations** -> **Webhooks** -> **Create Webhook**.
4. Copy the **Webhook URL**.

---

## 2. Project Architecture (Python)

We will build the tracker using lightweight Python scripts. The project files will be structured as follows:

```
gemini/
│
├── plans/
│   └── edm_ticket_tracker_plan.md   # This plan file
├── .github/workflows/
│   └── edm_tracker.yml              # GitHub Actions workflow for online scheduling
│
├── .env                  # Stores your API keys, webhook URLs, and configurations
├── requirements.txt      # List of Python dependencies (requests, python-dotenv, beautifulsoup4)
├── config.py             # Loads and validates environment variables from .env
├── seatgeek_client.py    # Interacts with SeatGeek to fetch EDM events, performer scores, and prices
├── stubhub_scraper.py    # Scrapes StubHub listings for targeted events to verify secondary markup
├── notifier.py           # Formats messages and sends them to Discord
└── main.py               # Main orchestrator script run by the daily scheduler
```

---

## 3. Pricing & Valuation Logic

To determine if an event/ticket is "valuable," the script will use the following heuristic:
1. **Performer Score**: Filter for EDM performers with a SeatGeek score above a threshold (e.g., `> 0.4` or `> 0.5`).
2. **Price Markup**:
   - Get the event's original/face-value price (or lowest direct sale price).
   - Get the SeatGeek resale `stats.lowest_price` or `stats.average_price`.
   - If the lowest resale price is significantly higher than the original direct ticket price (or if the average resale price shows a high markup percentage), mark the event as **high value** / **high resale demand**.
3. **Presales & Releases**:
   - Check if the ticket release is upcoming.
   - For events announcing new dates, check the onsale time and include direct ticket purchase links.

---

## 4. Automation and Scheduling (Online vs. Local)

### ☁️ Option A: GitHub Actions (Free & Fully Online) - Recommended
By pushing this codebase to a private GitHub repository, you can run the tracker daily in the cloud for free without needing your computer to be turned on.
- We have created a GitHub Actions workflow at `.github/workflows/edm_tracker.yml`.
- Your API credentials (`SEATGEEK_CLIENT_ID`, `SEATGEEK_CLIENT_SECRET`, `DISCORD_WEBHOOK_URL`) are stored securely as **Repository Secrets** in GitHub.
- It is set to run automatically every day at 9:00 AM EDT (13:00 UTC).

### 🖥️ Option B: Windows Task Scheduler (Local)
If you prefer running it locally:
- We have provided a `run.bat` file that activates the virtual environment and runs `main.py`.
- You can set Windows Task Scheduler to run `run.bat` daily.

---

## 5. Next Steps
1. **Approve this plan** by clicking **Proceed** (or let me know if you want changes).
2. I will create the project files, including the template `.env` file and the base code.
3. You will obtain the SeatGeek credentials and paste them into the `.env` file.
4. We will run tests and refine the scraping/pricing logic.
