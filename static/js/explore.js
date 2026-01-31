// Explore Page Map Logic - Supports Google Maps and OpenStreetMap (Leaflet)

(function () {
    console.log('[Explore Map] Script loaded');

    let map = null;
    let markers = [];
    let userMarker = null;
    let infoWindow = null; // Used for Google Maps
    let leafletPopup = null; // Used for Leaflet

    // Check which map provider to use
    const useOSM = window.useOpenStreetMap === true;
    console.log(`[Explore Map] Using provider: ${useOSM ? 'OpenStreetMap (Leaflet)' : 'Google Maps'}`);

    function initMap() {
        if (useOSM) {
            initLeafletMap();
        } else {
            initGoogleMap();
        }
    }

    // ==========================================
    // LEAFLET (OPENSTREETMAP) INITIALIZATION
    // ==========================================
    function initLeafletMap() {
        console.log('[Explore Map] Initializing Leaflet Map...');
        const mapContainer = document.getElementById('mapView');
        if (!mapContainer) return;

        // Default to Mumbai
        const defaultLat = 19.076;
        const defaultLng = 72.8777;

        try {
            // Initialize Leaflet Map
            map = L.map('mapView').setView([defaultLat, defaultLng], 12);

            // Add OpenStreetMap Tile Layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            console.log('[Explore Map] Leaflet Map initialized successfully');

            // Load data
            fetchRoomsAndPlot();

            // Bind UI Controls
            setupUIControls();

        } catch (error) {
            console.error('[Explore Map] Error initializing Leaflet map:', error);
            mapContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: red;">Map Error: ${error.message}</div>`;
        }
    }

    // ==========================================
    // GOOGLE MAPS INITIALIZATION
    // ==========================================
    function initGoogleMap() {
        console.log('[Explore Map] Initializing Google Maps...');
        const mapContainer = document.getElementById('mapView');
        if (!mapContainer) return;

        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            console.error('[Explore Map] Google Maps API not loaded. Retrying in 500ms...');
            setTimeout(initGoogleMap, 500);
            return;
        }

        try {
            map = new google.maps.Map(mapContainer, {
                center: { lat: 19.076, lng: 72.8777 },
                zoom: 12,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true,
                styles: [
                    {
                        featureType: "poi",
                        elementType: "labels",
                        stylers: [{ visibility: "off" }]
                    }
                ]
            });

            infoWindow = new google.maps.InfoWindow();
            console.log('[Explore Map] Google Map initialized successfully');

            fetchRoomsAndPlot();
            setupUIControls();

        } catch (error) {
            console.error('[Explore Map] Error initializing Google map:', error);
            mapContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: red;">Map Error: ${error.message}</div>`;
        }
    }

    function setupUIControls() {
        // Bind Locate Me Button
        const locateBtn = document.getElementById('locateMeBtn');
        if (locateBtn) {
            locateBtn.addEventListener('click', locateUser);
        }

        // Bind Reset Button
        const resetBtn = document.getElementById('recenterMap');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (useOSM) {
                    map.setView([19.076, 72.8777], 12);
                } else {
                    map.setCenter({ lat: 19.076, lng: 72.8777 });
                    map.setZoom(12);
                }
                fetchRoomsAndPlot(); // Re-fetch default
            });
        }

        // Bind Search Input
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            // Setup datalist... (simplified for brevity, logic remains same)
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                const query = e.target.value.trim();
                debounceTimer = setTimeout(() => {
                    if (query.length > 0) {
                        fetchSearchResults(query);
                    } else {
                        fetchRoomsAndPlot();
                    }
                }, 300);
            });
        }

        // Bind Filters
        const propertyTypeFilter = document.getElementById('propertyTypeFilter');
        const sortFilter = document.getElementById('sortFilter');
        const budgetSlider = document.getElementById('budgetSlider');
        const budgetValue = document.getElementById('budgetValue');

        if (propertyTypeFilter) propertyTypeFilter.addEventListener('change', fetchRoomsAndPlot);
        if (sortFilter) sortFilter.addEventListener('change', fetchRoomsAndPlot);
        if (budgetSlider) {
            budgetSlider.addEventListener('input', (e) => {
                if (budgetValue) budgetValue.textContent = `₹${parseInt(e.target.value).toLocaleString()}`;
            });
            budgetSlider.addEventListener('change', fetchRoomsAndPlot);
        }
    }

    // ==========================================
    // SHARED LOGIC
    // ==========================================

    async function fetchSearchResults(query) {
        try {
            console.log(`[Explore Map] Searching for: ${query}`);

            // Use the same API as home page with q parameter
            const propertyType = document.getElementById('propertyTypeFilter')?.value || '';
            const sort = document.getElementById('sortFilter')?.value || 'price_asc';
            const maxRent = document.getElementById('budgetSlider')?.value || '';

            const params = new URLSearchParams({
                limit: 50,
                q: query,
                property_type: propertyType,
                sort: sort
            });
            if (maxRent) params.append('max_rent', maxRent);

            const response = await fetch(`/api/rooms?${params.toString()}`);
            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            const rooms = data.rooms || [];
            console.log(`[Explore Map] Found ${rooms.length} matches for "${query}"`);
            plotRooms(rooms);

        } catch (error) {
            console.error('[Explore Map] Search error:', error);
        }
    }

    function locateUser() {
        const locateBtn = document.getElementById('locateMeBtn');
        const originalText = locateBtn ? locateBtn.innerHTML : 'Locate Me';

        if (locateBtn) {
            locateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
            locateBtn.disabled = true;
        }

        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            resetLocateBtn(locateBtn, originalText);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                if (useOSM) {
                    // Leaflet
                    if (userMarker) map.removeLayer(userMarker);

                    // Custom blue dot icon for user
                    const userIcon = L.divIcon({
                        className: 'user-location-marker',
                        html: '<div style="width: 12px; height: 12px; background: #2563eb; border: 2px solid white; border-radius: 50%; box-shadow: 0 0 0 2px #2563eb;"></div>',
                        iconSize: [16, 16],
                        iconAnchor: [8, 8]
                    });

                    userMarker = L.marker([lat, lng], { icon: userIcon }).addTo(map);
                    userMarker.bindPopup('<b>You are here</b>').openPopup();
                    map.setView([lat, lng], 14);

                } else {
                    // Google Maps
                    const userPos = { lat, lng };
                    if (userMarker) userMarker.setMap(null);

                    userMarker = new google.maps.Marker({
                        position: userPos,
                        map: map,
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 10,
                            fillColor: '#2563eb',
                            fillOpacity: 1,
                            strokeColor: '#ffffff',
                            strokeWeight: 3
                        },
                        title: 'Your Location'
                    });

                    infoWindow.setContent('<b>You are here</b>');
                    infoWindow.open(map, userMarker);
                    map.setCenter(userPos);
                    map.setZoom(14);
                }

                resetLocateBtn(locateBtn, originalText);
            },
            (error) => {
                console.error('[Explore Map] Location error:', error);
                alert('Unable to retrieve your location.');
                resetLocateBtn(locateBtn, originalText);
            }
        );
    }

    function resetLocateBtn(btn, text) {
        if (btn) {
            btn.innerHTML = text;
            btn.disabled = false;
        }
    }

    async function fetchRoomsAndPlot() {
        try {
            console.log('[Explore Map] Fetching rooms...');
            const propertyType = document.getElementById('propertyTypeFilter')?.value || '';
            const sort = document.getElementById('sortFilter')?.value || 'price_asc';
            const maxRent = document.getElementById('budgetSlider')?.value || '';

            const params = new URLSearchParams({
                limit: 50,
                property_type: propertyType,
                sort: sort
            });
            if (maxRent) params.append('max_rent', maxRent);

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
        if (!map) return;

        // Clear existing markers
        if (useOSM) {
            markers.forEach(mark => map.removeLayer(mark));
        } else {
            markers.forEach(mark => mark.setMap(null));
        }
        markers = [];

        // Setup bounds
        let latLngBounds = useOSM ? L.latLngBounds() : new google.maps.LatLngBounds();
        let hasPoints = false;

        const listContainer = document.getElementById('roomsList');
        if (listContainer) listContainer.innerHTML = '';

        rooms.forEach((room, index) => {
            if (room.latitude && room.longitude) {
                const lat = parseFloat(room.latitude);
                const lng = parseFloat(room.longitude);

                // Build sidebar card
                if (listContainer) {
                    const card = createSidebarCard(room);
                    listContainer.appendChild(card);

                    // Click handler for sidebar card
                    card.addEventListener('click', () => {
                        // Highlight
                        document.querySelectorAll('.room-card-sidebar').forEach(c => c.classList.remove('active'));
                        card.classList.add('active');

                        if (useOSM) {
                            map.setView([lat, lng], 16);
                            // Find marker and open popup - (simplified) just creating new popup for flow
                            L.popup()
                                .setLatLng([lat, lng])
                                .setContent(createPopupContent(room))
                                .openOn(map);
                        } else {
                            // Find specific google marker logic needed if we want exact marker ref, 
                            // or just create infoWindow at location
                            map.panTo({ lat, lng });
                            map.setZoom(16);
                            infoWindow.setContent(createPopupContent(room));
                            infoWindow.setPosition({ lat, lng });
                            infoWindow.open(map);
                        }
                    });
                }

                // Plot Marker on Map
                if (useOSM) {
                    // Leaflet Marker
                    const customIcon = L.divIcon({
                        className: 'custom-room-marker',
                        html: `<div style="background-color: #dc2626; width: 30px; height: 30px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
                                <i class="fas fa-home" style="font-size: 14px;"></i>
                               </div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 30],
                        popupAnchor: [0, -30]
                    });

                    const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
                    marker.bindPopup(createPopupContent(room));
                    markers.push(marker);
                    latLngBounds.extend([lat, lng]);
                    hasPoints = true;

                } else {
                    // Google Marker
                    const position = { lat, lng };
                    const marker = new google.maps.Marker({
                        position: position,
                        map: map,
                        title: room.title,
                        icon: {
                            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                                <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M18 0C10.8 0 5 5.8 5 13c0 9.75 13 23 13 23s13-13.25 13-23c0-7.2-5.8-13-13-13z" fill="#dc2626"/>
                                    <circle cx="18" cy="13" r="6" fill="white"/>
                                </svg>
                            `),
                            scaledSize: new google.maps.Size(36, 36),
                            anchor: new google.maps.Point(18, 36)
                        }
                    });

                    marker.addListener('click', () => {
                        infoWindow.setContent(createPopupContent(room));
                        infoWindow.open(map, marker);
                    });

                    markers.push(marker);
                    latLngBounds.extend(position);
                    hasPoints = true;
                }
            }
        });

        if (hasPoints) {
            if (useOSM) {
                map.fitBounds(latLngBounds, { padding: [50, 50] });
            } else {
                map.fitBounds(latLngBounds);
            }
        } else if (listContainer) {
            listContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">No rooms found matching your criteria.</div>';
        }
    }

    function createPopupContent(room) {
        return `
            <div style="min-width: 200px; padding: 4px; font-family: 'Poppins', sans-serif;">
                <h4 style="margin: 0 0 5px 0; color: #dc2626; font-size: 14px; font-weight: 600;">${room.title}</h4>
                <p style="margin: 0; font-weight: bold; font-size: 16px;">₹${room.price.toLocaleString()}/mo</p>
                <p style="margin: 2px 0 8px 0; font-size: 12px; color: #666;"><i class="fas fa-map-marker-alt"></i> ${room.location}</p>
                <div style="display: flex; gap: 8px;">
                    <a href="/room/${room.id}" style="flex: 1; text-align: center; padding: 6px; border: 1px solid #2563eb; color: #2563eb; text-decoration: none; border-radius: 4px; font-size: 12px;">View</a>
                    <a href="/book/${room.id}" style="flex: 1; text-align: center; padding: 6px; background: #dc2626; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: 600;">Book Now</a>
                </div>
            </div>
        `;
    }

    function createSidebarCard(room) {
        const card = document.createElement('div');
        card.className = 'room-card-sidebar';
        card.innerHTML = `
            <img src="${room.image_url}" alt="${room.title}" class="sidebar-card-img" onerror="this.src='https://via.placeholder.com/100?text=Room'">
            <div class="sidebar-card-content">
                <h4 class="sidebar-card-title">${room.title}</h4>
                <div class="sidebar-card-price">₹${room.price.toLocaleString()}<span style="font-size: 0.8em; color: #64748b; font-weight: 400;">/mo</span></div>
                <div class="sidebar-card-meta">
                    <i class="fas fa-map-marker-alt"></i> ${room.location}
                </div>
                <div class="sidebar-card-meta">
                    <i class="fas fa-bed"></i> ${room.property_type} • ${room.available_slots || 0} slots left
                </div>
                <a href="/book/${room.id}" class="sidebar-book-btn" style="display: block; width: 100%; text-align: center; margin-top: 10px; padding: 8px; background: #dc2626; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">
                    Book Now
                </a>
            </div>
        `;
        return card;
    }

    // Expose initialization globally
    window.initExploreMap = initMap;

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMap);
    } else {
        initMap();
    }

})();