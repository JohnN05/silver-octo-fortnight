# Raspberry Pi SSH Connection Rule

This rule stores the SSH connection and environment details for the Raspberry Pi 3 hosting the EDM Ticket Tracker program.

## Connection Details
- **IP Address:** `192.168.1.202`
- **Username:** `johnng0511`
- **Hostname:** `jong`
- **Port:** `22` (SSH)

## How to Run Commands on the Pi from Windows
To execute commands or check logs on the Raspberry Pi from the host, run:
```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no johnng0511@192.168.1.202 "<command>"
```

## Setup & Environment Details
- **Project Directory on Pi:** `/home/johnng0511/silver-octo-fortnight`
- **Active Virtual Environment:** `.venv` (located at `/home/johnng0511/silver-octo-fortnight/.venv`)
- **Scheduled Cron Job:**
  ```cron
  0 9,18 * * * cd /home/johnng0511/silver-octo-fortnight && .venv/bin/python main.py >> tracker.log 2>&1
  ```

Use this information to assist the user with checking logs, testing the script, or performing updates on the host device.
