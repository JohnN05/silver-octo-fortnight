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
        ? (events.reduce((sum, e) => sum + (e.analysis_roi || 0), 0) / events.length)
        : 0;
    const avgRoiPrefix = avgRoi >= 0 ? '+' : '';
    
    document.getElementById("global-stats").textContent = 
        `Active Scanned: ${events.length} | Critical: ${criticalCount} | Avg ROI: ${avgRoiPrefix}${avgRoi.toFixed(1)}%`;
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
        const rating = ["CRITICAL","HIGH","MEDIUM","LOW"].includes(event.analysis_rating)
            ? event.analysis_rating : "LOW";
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

        // Safe URL validation helper
        function safeUrl(raw) {
            if (!raw) return null;
            try { const u = new URL(raw); return (u.protocol === 'https:' || u.protocol === 'http:') ? raw : null; }
            catch { return null; }
        }

        // Build cells with DOM API — no innerHTML for API-supplied strings
        // Cell 1: Event / Artist
        const td1 = document.createElement("td");
        const eventCell = document.createElement("div");
        eventCell.className = "event-cell";
        const dot = document.createElement("span");
        dot.className = `status-dot dot-${rating}`;
        dot.title = `Rating: ${rating}`;
        const nameWrap = document.createElement("div");
        const artistSpan = document.createElement("span");
        artistSpan.className = "artist-name";
        artistSpan.textContent = event.artist || event.title || "Unknown Artist";
        const popSpan = document.createElement("span");
        popSpan.className = "popularity-label";
        popSpan.title = "SeatGeek Popularity Score";
        popSpan.textContent = `pop: ${scorePct}`;
        nameWrap.appendChild(artistSpan);
        nameWrap.appendChild(popSpan);
        eventCell.appendChild(dot);
        eventCell.appendChild(nameWrap);
        td1.appendChild(eventCell);

        // Cell 2: Venue
        const td2 = document.createElement("td");
        td2.textContent = event.venue_name || event.venue || 'Unknown Venue';

        // Cell 3: Date
        const td3 = document.createElement("td");
        td3.className = "mono-data";
        td3.textContent = dateStr;

        // Cell 4: Face Value
        const td4 = document.createElement("td");
        td4.className = "mono-data";
        td4.style.textAlign = "right";
        td4.textContent = face;

        // Cell 5: Lowest Resale
        const td5 = document.createElement("td");
        td5.className = "mono-data";
        td5.style.textAlign = "right";
        td5.textContent = lowestResale;

        // Cell 6: ROI
        const td6 = document.createElement("td");
        td6.className = `mono-data ${roiClass} roi-value`;
        td6.style.textAlign = "right";
        td6.textContent = roiText;

        // Cell 7: Actions
        const td7 = document.createElement("td");
        td7.style.textAlign = "center";
        const actionCell = document.createElement("div");
        actionCell.className = "action-cell";
        const sgUrl = safeUrl(event.seatgeek_url || event.url);
        if (sgUrl) {
            const sgLink = document.createElement("a");
            sgLink.href = sgUrl;
            sgLink.target = "_blank";
            sgLink.rel = "noopener noreferrer";
            sgLink.className = "btn-sm btn-primary-sm";
            sgLink.textContent = "SeatGeek";
            actionCell.appendChild(sgLink);
        }
        const tmUrl = safeUrl(event.ticketmaster_url);
        if (tmUrl) {
            const tmLink = document.createElement("a");
            tmLink.href = tmUrl;
            tmLink.target = "_blank";
            tmLink.rel = "noopener noreferrer";
            tmLink.className = "btn-sm";
            tmLink.textContent = "Official";
            actionCell.appendChild(tmLink);
        }
        td7.appendChild(actionCell);

        tr.appendChild(td1);
        tr.appendChild(td2);
        tr.appendChild(td3);
        tr.appendChild(td4);
        tr.appendChild(td5);
        tr.appendChild(td6);
        tr.appendChild(td7);
        tbody.appendChild(tr);
    });
}

