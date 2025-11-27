// Explore Page Map Logic - Simplified and Robust

(function() {
    console.log('[Explore Map] Script loaded');

    let map = null;
    let markersLayer = null;
    let userMarker = null;

    function initMap() {
        console.log('[Explore Map] Initializing...');

        const mapContainer = document.getElementById('mapView');
        if (!mapContainer) {
            console.error('[Explore Map] Container #mapView not found');
            return;
        }

        if (typeof L === 'undefined') {
            console.error('[Explore Map] Leaflet (L) is not defined. Retrying in 500ms...');
            setTimeout(initMap, 500);
            return;
        }

        // Cleanup existing map if any
        if (map) {
            console.log('[Explore Map] Removing existing map instance');
            map.remove();
            map = null;
        }

        // Check if map is already initialized by another script (safety check)
        if (mapContainer._leaflet_id) {
             console.warn('[Explore Map] Map container already has a leaflet ID. Attempting to clear.');
             mapContainer._leaflet_id = null;
             mapContainer.innerHTML = '';
        }

        try {
            // Initialize Map
            map = L.map('mapView', {
                center: [19.076, 72.8777], // Mumbai
                zoom: 12,
                scrollWheelZoom: false // Disable scroll zoom by default for better UX
            });

            // Add Tile Layer - Using CartoDB Voyager for better reliability and aesthetics
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);

            // Add Markers Layer Group
            markersLayer = L.layerGroup().addTo(map);

            console.log('[Explore Map] Map initialized successfully');

            // Add a test marker to verify visibility
            L.marker([19.076, 72.8777])
                .addTo(markersLayer)
                .bindPopup('<b>Mumbai</b><br>Default Center')
                .openPopup();

            // Load real data
            fetchRoomsAndPlot();

            // Handle window resize
            window.addEventListener('resize', () => {
                map.invalidateSize();
            });
            
            // Force a resize after a short delay to fix rendering glitches
            setTimeout(() => {
                map.invalidateSize();
            }, 500);

            // Bind Locate Me Button
            const locateBtn = document.getElementById('locateMeBtn');
            if (locateBtn) {
                locateBtn.addEventListener('click', locateUser);
            }

            // Bind Search Input for Autocomplete
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                // Create datalist for autocomplete
                const datalist = document.createElement('datalist');
                datalist.id = 'college-suggestions';
                document.body.appendChild(datalist);
                searchInput.setAttribute('list', 'college-suggestions');

                // Fetch colleges
                fetch('/api/colleges')
                    .then(res => res.json())
                    .then(colleges => {
                        colleges.forEach(college => {
                            const option = document.createElement('option');
                            option.value = college;
                            datalist.appendChild(option);
                        });
                    })
                    .catch(err => console.error('Failed to load colleges:', err));

                let debounceTimer;
                searchInput.addEventListener('input', (e) => {
                    clearTimeout(debounceTimer);
                    const query = e.target.value.trim();
                    
                    debounceTimer = setTimeout(() => {
                        if (query.length > 0) {
                            fetchSearchResults(query);
                        } else {
                            fetchRoomsAndPlot(); // Reset to all rooms
                        }
                    }, 300); // 300ms debounce
                });
            }

            // Bind Filters
            const propertyTypeFilter = document.getElementById('propertyTypeFilter');
            const sortFilter = document.getElementById('sortFilter');
            const budgetSlider = document.getElementById('budgetSlider');
            const budgetValue = document.getElementById('budgetValue');

            if (propertyTypeFilter) {
                propertyTypeFilter.addEventListener('change', fetchRoomsAndPlot);
            }
            if (sortFilter) {
                sortFilter.addEventListener('change', fetchRoomsAndPlot);
            }
            if (budgetSlider) {
                budgetSlider.addEventListener('input', (e) => {
                    if (budgetValue) budgetValue.textContent = `₹${parseInt(e.target.value).toLocaleString()}`;
                });
                budgetSlider.addEventListener('change', fetchRoomsAndPlot);
            }

        } catch (error) {
            console.error('[Explore Map] Error initializing map:', error);
            mapContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: red;">Map Error: ${error.message}</div>`;
        }
    }

    async function fetchSearchResults(query) {
        try {
            console.log(`[Explore Map] Searching for: ${query}`);
            const response = await fetch(`/api/search/autocomplete?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Search failed');
            
            const data = await response.json();
            const rooms = data.results || [];
            
            console.log(`[Explore Map] Found ${rooms.length} matches`);
            plotRooms(rooms);
            
        } catch (error) {
            console.error('[Explore Map] Search error:', error);
        }
    }

    function locateUser() {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }

        const locateBtn = document.getElementById('locateMeBtn');
        const originalText = locateBtn.innerHTML;
        locateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
        locateBtn.disabled = true;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                if (userMarker) {
                    map.removeLayer(userMarker);
                }

                // Create a pulsing blue dot for user location
                const userIcon = L.divIcon({
                    className: 'user-location-marker',
                    html: '<div style="background-color: #2563eb; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.3);"></div>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                });

                userMarker = L.marker([lat, lng], { icon: userIcon }).addTo(map);
                userMarker.bindPopup('<b>You are here</b>').openPopup();

                map.setView([lat, lng], 14);
                
                locateBtn.innerHTML = originalText;
                locateBtn.disabled = false;
            },
            (error) => {
                console.error('[Explore Map] Location error:', error);
                alert('Unable to retrieve your location. Please check your permissions.');
                locateBtn.innerHTML = originalText;
                locateBtn.disabled = false;
            }
        );
    }

    async function fetchRoomsAndPlot() {
        try {
            console.log('[Explore Map] Fetching rooms...');
            
            // Gather filter values
            const propertyType = document.getElementById('propertyTypeFilter')?.value || '';
            const sort = document.getElementById('sortFilter')?.value || 'price_asc';
            const maxRent = document.getElementById('budgetSlider')?.value || '';
            
            const params = new URLSearchParams({
                limit: 50,
                property_type: propertyType,
                sort: sort
            });
            
            if (maxRent) {
                params.append('max_rent', maxRent);
            }

            const response = await fetch(`/api/rooms?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to fetch rooms');
            
            const data = await response.json();
            const rooms = data.rooms || [];
            
            console.log(`[Explore Map] Found ${rooms.length} rooms`);
            plotRooms(rooms);

        } catch (error) {
            console.error('[Explore Map] Error fetching rooms:', error);
        }
    }

    function plotRooms(rooms) {
        if (!map || !markersLayer) return;

        markersLayer.clearLayers();
        const bounds = [];
        const listContainer = document.getElementById('roomsList');
        if (listContainer) listContainer.innerHTML = '';

        rooms.forEach(room => {
            if (room.latitude && room.longitude) {
                // 1. Create Marker
                const marker = L.marker([room.latitude, room.longitude]);
                
                const popupContent = `
                    <div style="min-width: 200px;">
                        <h4 style="margin: 0 0 5px 0; color: #dc2626;">${room.title}</h4>
                        <p style="margin: 0; font-weight: bold;">₹${room.price}/mo</p>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">${room.location}</p>
                        <a href="/room/${room.id}" style="display: block; margin-top: 8px; color: #2563eb; text-decoration: none; font-weight: 600;">View Details &rarr;</a>
                    </div>
                `;
                
                marker.bindPopup(popupContent);
                markersLayer.addLayer(marker);
                bounds.push([room.latitude, room.longitude]);

                // 2. Create Sidebar Card
                if (listContainer) {
                    const card = document.createElement('div');
                    card.className = 'room-card-sidebar';
                    card.innerHTML = `
                        <img src="${room.image_url}" alt="${room.title}" class="sidebar-card-img">
                        <div class="sidebar-card-content">
                            <h4 class="sidebar-card-title">${room.title}</h4>
                            <div class="sidebar-card-price">₹${room.price.toLocaleString()}<span style="font-size: 0.8em; color: #64748b; font-weight: 400;">/mo</span></div>
                            <div class="sidebar-card-meta">
                                <i class="fas fa-map-marker-alt"></i> ${room.location}
                            </div>
                            <div class="sidebar-card-meta">
                                <i class="fas fa-bed"></i> ${room.property_type} • ${room.available_slots} slots left
                            </div>
                        </div>
                    `;

                    // Interaction: Click card -> Fly to map
                    card.addEventListener('click', () => {
                        // Highlight card
                        document.querySelectorAll('.room-card-sidebar').forEach(c => c.classList.remove('active'));
                        card.classList.add('active');

                        // Fly map
                        map.flyTo([room.latitude, room.longitude], 16, {
                            animate: true,
                            duration: 1.5
                        });
                        marker.openPopup();
                    });

                    listContainer.appendChild(card);
                }
            }
        });

        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [50, 50] });
        } else if (listContainer) {
            listContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">No rooms found matching your criteria.</div>';
        }
    }

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMap);
    } else {
        initMap();
    }

    // Expose for debugging
    window.exploreMapInstance = {
        init: initMap,
        getMap: () => map
    };

})();