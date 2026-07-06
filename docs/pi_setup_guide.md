# Raspberry Pi Setup Guide: EDM Ticket Tracker

This guide details how to set up the **EDM Ticket Tracker & Decoupled Dashboard** on your Raspberry Pi. The tracker is designed to run efficiently on low-resource hardware like a Raspberry Pi 3 or 4, executing daily scans and committing update results to the static web dashboard.

---

## 1. System Requirements & Dependencies

Before beginning, ensure your Raspberry Pi is connected to the internet and has the necessary system packages.

Run the following commands on your Raspberry Pi:
```bash
# Update package lists
sudo apt-get update

# Install Python 3, Virtual Environment support, Git, and SQLite3
sudo apt-get install -y python3 python3-pip python3-venv git sqlite3
```

---

## 2. Environment Variables (.env)

The application uses a `.env` file to securely store configuration settings and API credentials. You will need to create this file in the project's root directory.

### Required Environment Variables

| Variable | Description | Where to Get It / Example |
| :--- | :--- | :--- |
| `SEATGEEK_CLIENT_ID` | Client ID for SeatGeek API | [SeatGeek Developers Console](https://seatgeek.com/account/develop) |
| `SEATGEEK_CLIENT_SECRET` | Client Secret for SeatGeek API | [SeatGeek Developers Console](https://seatgeek.com/account/develop) |
| `DISCORD_WEBHOOK_URL` | Webhook URL for Discord notifications channel | Discord Channel Settings > Integrations > Webhooks |

### Optional Configuration Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `TICKETMASTER_API_KEY` | *None* | Official Ticketmaster developer API key (used for verified ticket face values) |
| `LATITUDE` | `39.1434` | Latitude center point of event scans (Default: Gaithersburg, MD) |
| `LONGITUDE` | `-77.2014` | Longitude center point of event scans |
| `RADIUS` | `45mi` | Radius of scan search area (e.g., `50mi`, `10km`) |
| `POPULARITY_THRESHOLD`| `0.40` | Min performer score (0.0 to 1.0) to qualify for notification |
| `MARKUP_THRESHOLD` | `1.15` | Min expected resale-to-face ratio (e.g., `1.15` is a 15% markup) |

---

## 3. Step-by-Step Installation

### Step A: Clone the Codebase
Because the script automatically pushes dashboard data back to GitHub, it is highly recommended to clone the repository using **SSH** rather than HTTPS.

1. Generate an SSH Key on your Raspberry Pi (if you haven't already):
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
   *Press Enter to accept defaults.*
2. Start the SSH Agent and add your private key:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```
3. Print the public key and add it to your GitHub Profile settings (**Settings > SSH and GPG keys**):
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
4. Clone the repository using SSH:
   ```bash
   git clone git@github.com:JohnN05/silver-octo-fortnight.git
   cd silver-octo-fortnight
   ```

### Step B: Set Up the Virtual Environment
Navigate to the project root on the Pi and create a virtual environment to keep python packages isolated:

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install all requirements
pip install -r requirements.txt
```

### Step C: Create the `.env` File
Create a new `.env` file inside the project directory:

```bash
nano .env
```
Copy and paste the configuration template, replacing values with your credentials:
```ini
# SeatGeek API Credentials
SEATGEEK_CLIENT_ID=your_seatgeek_client_id_here
SEATGEEK_CLIENT_SECRET=your_seatgeek_client_secret_here

# Ticketmaster API Credentials (Optional)
TICKETMASTER_API_KEY=your_ticketmaster_api_key_here

# Discord Webhook Configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Optional Scanner Settings
LATITUDE=39.1434
LONGITUDE=-77.2014
RADIUS=45mi
POPULARITY_THRESHOLD=0.40
MARKUP_THRESHOLD=1.15
```
*Save and close (in nano, press `Ctrl+O`, `Enter`, then `Ctrl+X`).*

---

## 4. Verification & Testing

Verify that your environment, database, and notifications are correctly configured by running a test scan:

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Run the tracker in test mode using mock SeatGeek data
python3 main.py --test
```

### Expected Output:
- The script initializes `edm_tracker.db` SQLite database (created automatically if not present).
- Performs a simulated ETL run using mock event information.
- Sends a test alert directly to your Discord webhook.
- Exports mock statistics to `docs/data.json` inside the repository.
- Attempts to push the change to GitHub (will skip if git status shows no modification or remote connection is not set up).

---

## 5. Daily Automation (Cron Scheduler)

Configure the script to run automatically every morning using the Unix cron scheduler.

1. Open the cron editor:
   ```bash
   crontab -e
   ```
2. Add the following line at the bottom to run the scraper daily at 6:00 AM local time:
   ```cron
   0 6 * * * cd /home/pi/silver-octo-fortnight && .venv/bin/python main.py >> tracker.log 2>&1
   ```
   *(Be sure to replace `/home/pi/silver-octo-fortnight` with the actual path where you cloned the repository).*

---

## 6. GitHub Pages Dashboard Configuration

To make the dashboard accessible online:
1. Navigate to your repository page on GitHub (`https://github.com/JohnN05/silver-octo-fortnight`).
2. Click on **Settings** > **Pages** (under the Code and automation section).
3. Set **Source** to `Deploy from a branch`.
4. Under **Branch**, select `main` and change the directory drop-down from `/ (root)` to `/docs`.
5. Click **Save**.

Within a few minutes, GitHub will build the site, which will be accessible at:
`https://JohnN05.github.io/silver-octo-fortnight/`
