# Decoupled Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a premium, mobile-responsive static web dashboard hosted on GitHub Pages that reads from a dynamically generated JSON file updated by the ETL pipeline.

**Architecture:** The ETL pipeline will export its analysis to `docs/data.json` and push it to the main branch. A static HTML/CSS/JS app sitting in the `docs/` folder will fetch this JSON and render the data with a premium aesthetic. The Discord notification will link to this GitHub Pages site.

**Tech Stack:** Python (Backend export & Git push subprocess), HTML5, Vanilla CSS (Dark mode, glassmorphism), Vanilla JavaScript.

## Global Constraints

- Must run smoothly on a Raspberry Pi 3 (no heavy Node.js build steps, just raw static files and python).
- The web app must use a sleek, ultra-minimalist design (matte charcoal background, no glows or gradients, hairline rule borders, clean typography, and amplifier LED-style status dots).
- The GitHub Pages URL is expected to be `https://JohnN05.github.io/silver-octo-fortnight/` (assuming serving from `/docs` directory on the `main` branch).

---

### Task 1: Export Data to JSON

**Files:**
- Modify: `notifier.py`
- Modify: `main.py`

**Interfaces:**
- Consumes: `events_with_analysis` from `etl_pipeline.py`.
- Produces: `docs/data.json` containing the event data.

- [ ] **Step 1: Write JSON export function in `notifier.py`**

Modify `notifier.py` to add a new function for exporting data:

```python
import json
import os

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
```

- [ ] **Step 2: Call JSON export in `main.py`**

Update `main.py` to call `generate_json_data` and trigger a git push:

```python
import subprocess

# ... inside run_tracker(), after notifier.generate_markdown_report() ...
        notifier.generate_json_data(events_to_notify)
        
        # Auto-commit and push the data update
        try:
            subprocess.run(["git", "add", "docs/data.json"], check=True)
            subprocess.run(["git", "commit", "-m", "chore: update dashboard data [skip ci]"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            logger.info("Successfully pushed updated data.json to GitHub")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git push failed (normal if no changes or running locally): {e}")
```

### Task 2: Build the Premium Dashboard UI (HTML & CSS)

**Files:**
- Create: `docs/index.html`
- Create: `docs/style.css`

**Interfaces:**
- Consumes: None
- Produces: The UI structure and styling that `app.js` will populate.

- [ ] **Step 1: Create `docs/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decibel Dispatch // EDM Ticket Valuation</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <h1>DECIBEL DISPATCH</h1>
                <span class="sub-brand">// EDM TICKET VALUATION ENGINE</span>
            </div>
            <div class="meta-status">
                <span id="last-updated">Last scan: Loading...</span>
                <span id="global-stats">Stats: Loading...</span>
            </div>
        </header>

        <section class="controls">
            <div class="filter-group">
                <span class="control-label">Venue:</span>
                <div class="filter-buttons" id="venue-filters">
                    <button class="filter-btn active" data-venue="all">All</button>
                </div>
            </div>
            <div class="filter-group">
                <span class="control-label">Sort By:</span>
                <div class="filter-buttons" id="sort-filters">
                    <button class="filter-btn active" data-sort="roi">ROI %</button>
                    <button class="filter-btn" data-sort="date">Date</button>
                    <button class="filter-btn" data-sort="popularity">Artist Popularity</button>
                </div>
            </div>
        </section>

        <main>
            <div class="table-container">
                <table class="valuation-table">
                    <thead>
                        <tr>
                            <th align="left">Event / Artist</th>
                            <th align="left">Venue</th>
                            <th align="left">Date</th>
                            <th align="right">Face Value</th>
                            <th align="right">Lowest Resale</th>
                            <th align="right">ROI Potential</th>
                            <th align="center">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="event-rows">
                        <tr>
                            <td colspan="7" align="center" class="loading-state">Loading analysis data...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </main>
    </div>
    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create `docs/style.css`**

```css
:root {
    --bg-main: #0a0b0d;        /* Dark matte background */
    --panel-bg: #111215;       /* Card/Header fill */
    --border-color: #1a1d24;   /* Fine divider border */
    --text-primary: #f8f9fa;   /* Crisp off-white */
    --text-muted: #6e7681;     /* Medium slate gray */
    
    /* Muted Status LED colors */
    --status-critical: #ef4444; /* Coral red */
    --status-high: #f59e0b;     /* Amber */
    --status-medium: #3b82f6;   /* Blue */
    --status-low: #6b7280;      /* Gray */
    
    --success-green: #10b981;  /* Soft green for positive ROI */
    --alert-red: #ef4444;      /* Soft red for negative ROI */
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-main);
    color: var(--text-primary);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 3rem 2rem;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}

.brand h1 {
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}

.brand .sub-brand {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
}

.meta-status {
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
}

.meta-status span {
    display: block;
    margin-top: 0.25rem;
}

.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 2rem;
    margin-bottom: 2rem;
}

.filter-group {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.control-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    font-weight: 500;
}

.filter-buttons {
    display: flex;
    gap: 0.5rem;
}

.filter-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 0.35rem 0.75rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.15s ease;
}

.filter-btn:hover {
    border-color: var(--text-primary);
}

.filter-btn.active {
    background: var(--text-primary);
    color: var(--bg-main);
    border-color: var(--text-primary);
    font-weight: 500;
}

.table-container {
    width: 100%;
    overflow-x: auto;
}

.valuation-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.valuation-table th {
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.valuation-table td {
    padding: 1.25rem 1rem;
    border-bottom: 1px solid var(--border-color);
    vertical-align: middle;
}

.valuation-table tbody tr {
    transition: background-color 0.15s ease;
}

.valuation-table tbody tr:hover {
    background-color: rgba(255, 255, 255, 0.02);
}

/* Event column */
.event-cell {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-CRITICAL { background-color: var(--status-critical); }
.dot-HIGH { background-color: var(--status-high); }
.dot-MEDIUM { background-color: var(--status-medium); }
.dot-LOW { background-color: var(--status-low); }

.artist-name {
    font-weight: 500;
}

.popularity-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-left: 0.5rem;
}

.mono-data {
    font-family: 'JetBrains Mono', monospace;
}

.roi-positive {
    color: var(--success-green);
}

.roi-negative {
    color: var(--alert-red);
}

/* Action buttons */
.action-cell {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
}

.btn-sm {
    text-decoration: none;
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    transition: all 0.15s ease;
}

.btn-sm:hover {
    background: var(--text-primary);
    color: var(--bg-main);
    border-color: var(--text-primary);
}

.btn-primary-sm {
    border-color: var(--text-primary);
}

.loading-state, .empty-state {
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
    padding: 3rem 0;
}

@media (max-width: 768px) {
    .container {
        padding: 1.5rem 1rem;
    }
    header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    .meta-status {
        text-align: left;
    }
    .controls {
        flex-direction: column;
        gap: 1rem;
    }
    .valuation-table th, .valuation-table td {
        padding: 0.75rem 0.5rem;
    }
}
```

### Task 3: Build the Dashboard Logic (JavaScript)

**Files:**
- Create: `docs/app.js`

**Interfaces:**
- Consumes: `docs/data.json` via fetch API.
- Produces: Hydrated DOM elements inside `#event-grid`.

- [ ] **Step 1: Write `docs/app.js` to fetch and render data**

```javascript
let allEvents = [];
let activeVenueFilter = 'all';
let activeSortFilter = 'roi';

document.addEventListener("DOMContentLoaded", () => {
    fetch("data.json")
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            const date = new Date(data.last_updated);
            document.getElementById("last-updated").textContent = `Last scan: ${date.toLocaleString()}`;
            
            allEvents = data.events || [];
            
            // Build venue filter options dynamically
            populateVenueFilters(allEvents);
            
            // Render initial data
            filterAndRender();
            
            // Set up event listeners
            setupEventListeners();
        })
        .catch(err => {
            console.error("Error loading data:", err);
            document.getElementById("event-rows").innerHTML = `
                <tr>
                    <td colspan="7" align="center" class="empty-state">Error loading scan database. Ensure data.json exists.</td>
                </tr>
            `;
        });
});

function populateVenueFilters(events) {
    const filterContainer = document.getElementById("venue-filters");
    const venues = new Set();
    
    events.forEach(e => {
        if (e.venue_name) {
            venues.add(e.venue_name);
        }
    });
    
    venues.forEach(venue => {
        const btn = document.createElement("button");
        btn.className = "filter-btn";
        btn.setAttribute("data-venue", venue);
        btn.textContent = venue;
        filterContainer.appendChild(btn);
    });
}

function setupEventListeners() {
    // Venue Filters
    document.getElementById("venue-filters").addEventListener("click", (e) => {
        if (e.target.classList.contains("filter-btn")) {
            document.querySelectorAll("#venue-filters .filter-btn").forEach(btn => btn.classList.remove("active"));
            e.target.classList.add("active");
            activeVenueFilter = e.target.getAttribute("data-venue");
            filterAndRender();
        }
    });
    
    // Sort Filters
    document.getElementById("sort-filters").addEventListener("click", (e) => {
        if (e.target.classList.contains("filter-btn")) {
            document.querySelectorAll("#sort-filters .filter-btn").forEach(btn => btn.classList.remove("active"));
            e.target.classList.add("active");
            activeSortFilter = e.target.getAttribute("data-sort");
            filterAndRender();
        }
    });
}

function filterAndRender() {
    let filtered = [...allEvents];
    
    // 1. Filter by Venue
    if (activeVenueFilter !== 'all') {
        filtered = filtered.filter(e => e.venue_name === activeVenueFilter);
    }
    
    // 2. Sort Events
    if (activeSortFilter === 'roi') {
        filtered.sort((a, b) => (b.analysis_roi || 0) - (a.analysis_roi || 0));
    } else if (activeSortFilter === 'date') {
        filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
    } else if (activeSortFilter === 'popularity') {
        filtered.sort((a, b) => (b.artist_score || 0) - (a.artist_score || 0));
    }
    
    // 3. Update global statistics
    updateGlobalStats(filtered);
    
    // 4. Render Table
    renderTable(filtered);
}

function updateGlobalStats(events) {
    const criticalCount = events.filter(e => e.analysis_rating === "CRITICAL").length;
    const avgRoi = events.length > 0 
        ? (events.reduce((sum, e) => sum + (e.analysis_roi || 0), 0) / events.length).toFixed(1) 
        : "0.0";
    
    document.getElementById("global-stats").textContent = 
        `Active Scanned: ${events.length} | Critical: ${criticalCount} | Avg ROI: +${avgRoi}%`;
}

function renderTable(events) {
    const tbody = document.getElementById("event-rows");
    tbody.innerHTML = "";
    
    if (events.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" align="center" class="empty-state">No upcoming opportunities found matching filters.</td>
            </tr>
        `;
        return;
    }
    
    events.forEach(event => {
        const tr = document.createElement("tr");
        
        // Performer popularity & rating LED
        const rating = event.analysis_rating || "LOW";
        const scorePct = event.artist_score ? `${Math.round(event.artist_score * 100)}%` : 'N/A';
        
        // Price values
        const face = event.face_value ? `$${event.face_value.toFixed(2)}` : 'N/A';
        const lowestResale = event.resale_lowest ? `$${event.resale_lowest.toFixed(2)}` : 'N/A';
        
        // ROI formatting
        const roi = event.analysis_roi || 0.0;
        const roiClass = roi >= 0 ? 'roi-positive' : 'roi-negative';
        const roiPrefix = roi >= 0 ? '+' : '';
        const roiText = `${roiPrefix}${roi.toFixed(1)}%`;
        
        // Date formatting
        let dateStr = 'TBD';
        if (event.date) {
            const d = new Date(event.date);
            dateStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        }
        
        tr.innerHTML = `
            <td>
                <div class="event-cell">
                    <span class="status-dot dot-${rating}" title="Rating: ${rating}"></span>
                    <div>
                        <span class="artist-name">${event.artist || event.title}</span>
                        <span class="popularity-label" title="SeatGeek Popularity Score">pop: ${scorePct}</span>
                    </div>
                </div>
            </td>
            <td>${event.venue_name || event.venue || 'Unknown Venue'}</td>
            <td class="mono-data">${dateStr}</td>
            <td align="right" class="mono-data">${face}</td>
            <td align="right" class="mono-data">${lowestResale}</td>
            <td align="right" class="mono-data ${roiClass} font-weight-bold">${roiText}</td>
            <td align="center">
                <div class="action-cell">
                    <a href="${event.seatgeek_url || event.url}" target="_blank" class="btn-sm btn-primary-sm">SeatGeek</a>
                    ${event.ticketmaster_url ? `<a href="${event.ticketmaster_url}" target="_blank" class="btn-sm">Official</a>` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
```

### Task 4: Update Discord Notification Link

**Files:**
- Modify: `notifier.py`

**Interfaces:**
- Consumes: `config.py` (optional) or hardcoded github pages URL.
- Produces: A Discord message that points to the new dashboard.

- [ ] **Step 1: Add Dashboard Link to Discord Alerts**

Update `notifier.py` in the `send_discord_notification` function to include the dashboard link at the bottom of the embed list.

```python
    # ... after adding all event embeds inside send_discord_notification ...
    
    # Add a final embed linking to the dashboard
    dashboard_url = "https://JohnN05.github.io/silver-octo-fortnight/"
    embeds.append({
        "title": "📊 View Full Pricing Dashboard",
        "url": dashboard_url,
        "description": "Click here to view interactive charts, analysis, and more details on any device.",
        "color": 0x2C3E50
    })
    
    payload = {"embeds": embeds}
    # ... sends payload ...
```
