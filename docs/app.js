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
        const face = event.face_value ? \`$\${event.face_value.toFixed(2)}\` : 'N/A';
        const lowestResale = event.resale_lowest ? \`$\${event.resale_lowest.toFixed(2)}\` : 'N/A';
        
        // ROI formatting
        const roi = event.analysis_roi || 0.0;
        const roiClass = roi >= 0 ? 'roi-positive' : 'roi-negative';
        const roiPrefix = roi >= 0 ? '+' : '';
        const roiText = \`\${roiPrefix}\${roi.toFixed(1)}%\`;
        
        // Date formatting
        let dateStr = 'TBD';
        if (event.date) {
            const d = new Date(event.date);
            dateStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        }
        
        tr.innerHTML = \`
            <td>
                <div class="event-cell">
                    <span class="status-dot dot-\${rating}" title="Rating: \${rating}"></span>
                    <div>
                        <span class="artist-name">\${event.artist || event.title}</span>
                        <span class="popularity-label" title="SeatGeek Popularity Score">pop: \${scorePct}</span>
                    </div>
                </div>
            </td>
            <td>\${event.venue_name || event.venue || 'Unknown Venue'}</td>
            <td class="mono-data">\${dateStr}</td>
            <td align="right" class="mono-data">\${face}</td>
            <td align="right" class="mono-data">\${lowestResale}</td>
            <td align="right" class="mono-data \${roiClass} font-weight-bold">\${roiText}</td>
            <td align="center">
                <div class="action-cell">
                    <a href="\${event.seatgeek_url || event.url}" target="_blank" class="btn-sm btn-primary-sm">SeatGeek</a>
                    \${event.ticketmaster_url ? \`<a href="\${event.ticketmaster_url}" target="_blank" class="btn-sm">Official</a>\` : ''}
                </div>
            </td>
        \`;
        tbody.appendChild(tr);
    });
}
