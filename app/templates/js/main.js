var map = L.map('map', { zoomControl: false }).setView([51.505, -0.09], 13);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

// Default zoom control sits top-left, which collides with the search panel.
L.control.zoom({ position: 'topright' }).addTo(map);

var popup = L.popup();
var currentRouteLine = null;

let activeInputId = 'from-input';

function setActiveInput(inputId) {
    activeInputId = inputId;
    document.querySelectorAll('.map-pick-btn').forEach(b => {
        if (b.getAttribute('data-target') === inputId) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });
}

// Setup map pick buttons
document.querySelectorAll('.map-pick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        setActiveInput(btn.getAttribute('data-target'));
        document.getElementById(activeInputId).focus();
    });
});

async function searchRoute() {
    const fromInput = document.getElementById('from-input');
    const toInput = document.getElementById('to-input');
    const routeType = document.querySelector('input[name="route-type"]:checked').value;
    const travelMode = document.querySelector('input[name="travel-mode"]:checked').value;

    const fromLat = fromInput.dataset.lat;
    const fromLng = fromInput.dataset.lng;
    const toLat = toInput.dataset.lat;
    const toLng = toInput.dataset.lng;

    if (!fromLat || !fromLng || !toLat || !toLng) {
        alert("Please select both starting and destination points on the map.");
        return;
    }

    try {
        const response = await fetch(`/api/find_route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                from_: { lat: fromLat, lng: fromLng }, 
                to: { lat: toLat, lng: toLng },
                routeType: routeType,
                travelMode: travelMode
            })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.status === "success" && data.path && data.path.length > 0) {
                // Clear previous route line if exists
                if (currentRouteLine) {
                    map.removeLayer(currentRouteLine);
                }

                currentRouteLine = L.polyline(data.path, {
                    color: '#1a73e8',
                    weight: 5,
                    opacity: 0.85,
                    routeName: "Route"
                })
                .bindTooltip(`${data.distance >= 1000 ? (data.distance / 1000).toFixed(1) + ' km' : data.distance.toFixed(0) + ' m'}`, {
                    permanent: true,
                    direction: 'center'
                })
                .addTo(map);
                map.fitBounds(currentRouteLine.getBounds(), { padding: [40, 40] });

                // Display statistics
                const statsPanel = document.getElementById('route-stats');
                if (statsPanel) {
                    statsPanel.style.display = 'block';

                    // Update Algorithm Badge
                    const algoBadge = document.getElementById('stat-algo-badge');
                    if (algoBadge) {
                        algoBadge.textContent = routeType === 'astar' ? 'A* search' : 'Dijkstra';
                    }

                    // Distance formatting
                    const distanceStr = data.distance >= 1000
                        ? `${(data.distance / 1000).toFixed(2)} km`
                        : `${data.distance.toFixed(0)} m`;
                    document.getElementById('stat-distance').textContent = distanceStr;

                    // Est. time formatting
                    const timeStr = data.time >= 60
                        ? `${Math.floor(data.time / 60)}h ${(data.time % 60).toFixed(0)}m`
                        : `${data.time.toFixed(1)} min`;
                    document.getElementById('stat-time').textContent = timeStr;

                    // Visited nodes
                    const visitedCount = data.nodes_visited_count ?? data.visited_nodes ?? 0;
                    document.getElementById('stat-visited-nodes').textContent = `${visitedCount}`;

                    // Execution time
                    let execTimeStr = '0 ms';
                    if (data.execution_time !== undefined) {
                        const ms = data.execution_time * 1000;
                        execTimeStr = ms < 1 ? `${ms.toFixed(2)} ms` : `${ms.toFixed(1)} ms`;
                    }
                    document.getElementById('stat-exec-time').textContent = execTimeStr;
                }
            } else {
                const statsPanel = document.getElementById('route-stats');
                if (statsPanel) statsPanel.style.display = 'none';
                alert(data.message || "No route found between the selected points.");
            }
        } else {
            alert("Error finding route.");
        }
    } catch (error) {
        console.error("Error finding route:", error);
        alert("Error finding route.");
    }
}

// Update active input when focused
document.getElementById('from-input').addEventListener('focus', () => setActiveInput('from-input'));
document.getElementById('to-input').addEventListener('focus', () => setActiveInput('to-input'));
document.getElementById('find-route-btn').addEventListener('click', () => searchRoute());

// Handle map clicks (Reverse Geocoding)
async function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("Loading address for " + e.latlng.toString() + "...")
        .openOn(map);

    try {
        const response = await fetch(`/api/reverse-geocode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: e.latlng.lat, lng: e.latlng.lng })
        });
        const data = await response.json();

        const activeInput = document.getElementById(activeInputId);
        activeInput.value = data.address;
        activeInput.dataset.lat = e.latlng.lat;
        activeInput.dataset.lng = e.latlng.lng;
        activeInput.focus();

        popup.setContent(`<strong>Address:</strong> ${data.address}<br><em>(Stub API response)</em>`);
    } catch (error) {
        popup.setContent("Error fetching address API.");
        console.error("Reverse geocoding error:", error);
    }
}
map.on('click', onMapClick);

// Handle search input typing (Search/Forward Geocoding)
let searchTimeout;
async function handleSearchInput(e) {
    const query = e.target.value;
    if (!query) return;

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        console.log(`Searching for: ${query}`);
        try {
            const response = await fetch(`/api/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            const data = await response.json();
            console.log("Search API response:", data);
            if (data.results && data.results.length > 0) {
                const firstResult = data.results[0];
                L.marker([firstResult.lat, firstResult.lng]).addTo(map)
                    .bindPopup(`Search Result: ${firstResult.name}`).openPopup();
                map.setView([firstResult.lat, firstResult.lng], 13);

                e.target.dataset.lat = firstResult.lat;
                e.target.dataset.lng = firstResult.lng;
                e.target.value = firstResult.address;
            }
        } catch (error) {
            console.error("Search error:", error);
        }
    }, 500); // 500ms debounce
}

document.getElementById('from-input').addEventListener('input', handleSearchInput);
document.getElementById('to-input').addEventListener('input', handleSearchInput);
