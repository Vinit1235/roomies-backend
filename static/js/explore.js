// Explore Page Map Logic - Google Maps Version

(function () {
    console.log('[Explore Map] Script loaded (Google Maps)');

    let map = null;
    let markers = [];
    let userMarker = null;
    let infoWindow = null;

    function initMap() {
        console.log('[Explore Map] Initializing Google Maps...');

        const mapContainer = document.getElementById('mapView');
        if (!mapContainer) {
            console.error('[Explore Map] Container #mapView not found');
            return;
        }

        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            console.error('[Explore Map] Google Maps API not loaded. Retrying in 500ms...');
            setTimeout(initMap, 500);
            return;
        }

        try {
            // Initialize Google Map
            map = new google.maps.Map(mapContainer, {
                center: { lat: 19.076, lng: 72.8777 }, // Mumbai
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

            // Create a single InfoWindow for reuse
            infoWindow = new google.maps.InfoWindow();

            console.log('[Explore Map] Google Map initialized successfully');

            // Load real data
            fetchRoomsAndPlot();

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
                    }, 300);
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
                const userPos = { lat, lng };

                if (userMarker) {
                    userMarker.setMap(null);
                }

                // Create a blue dot marker for user location
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

                // Show info window
                infoWindow.setContent('<b>You are here</b>');
                infoWindow.open(map, userMarker);

                map.setCenter(userPos);
                map.setZoom(14);

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
        if (!map) return;

        // Clear existing markers
        markers.forEach(marker => marker.setMap(null));
        markers = [];

        const bounds = new google.maps.LatLngBounds();
        const listContainer = document.getElementById('roomsList');
        if (listContainer) listContainer.innerHTML = '';

        rooms.forEach(room => {
            if (room.latitude && room.longitude) {
                const position = { lat: room.latitude, lng: room.longitude };

                // Create custom marker
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

                // InfoWindow content
                const popupContent = `
                    <div style="min-width: 200px; padding: 8px;">
                        <h4 style="margin: 0 0 5px 0; color: #dc2626; font-size: 14px;">${room.title}</h4>
                        <p style="margin: 0; font-weight: bold; font-size: 16px;">₹${room.price}/mo</p>
                        <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">${room.location}</p>
                        <div style="margin-top: 10px; display: flex; gap: 8px;">
                            <a href="/room/${room.id}" style="flex: 1; text-align: center; padding: 4px; border: 1px solid #2563eb; color: #2563eb; text-decoration: none; border-radius: 4px; font-size: 12px;">View</a>
                            <a href="/book/${room.id}" style="flex: 1; text-align: center; padding: 4px; background: #dc2626; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: bold;">Book Now</a>
                        </div>
                    </div>
                `;

                marker.addListener('click', () => {
                    infoWindow.setContent(popupContent);
                    infoWindow.open(map, marker);
                });

                markers.push(marker);
                bounds.extend(position);

                // Create Sidebar Card
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
                            <a href="/book/${room.id}" class="sidebar-book-btn" style="display: block; width: 100%; text-align: center; margin-top: 10px; padding: 8px; background: #dc2626; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">
                                Book Now
                            </a>
                        </div>
                    `;

                    // Interaction: Click card -> Pan to map
                    card.addEventListener('click', () => {
                        // Highlight card
                        document.querySelectorAll('.room-card-sidebar').forEach(c => c.classList.remove('active'));
                        card.classList.add('active');

                        // Pan map
                        map.panTo(position);
                        map.setZoom(16);
                        infoWindow.setContent(popupContent);
                        infoWindow.open(map, marker);
                    });

                    listContainer.appendChild(card);
                }
            }
        });

        if (markers.length > 0) {
            map.fitBounds(bounds);
        } else if (listContainer) {
            listContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">No rooms found matching your criteria.</div>';
        }
    }

    // Expose initMap globally for Google Maps callback
    window.initExploreMap = initMap;

    // Initialize on load if Google Maps already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (typeof google !== 'undefined') {
                initMap();
            }
        });
    } else {
        if (typeof google !== 'undefined') {
            initMap();
        }
    }

    // Expose for debugging
    window.exploreMapInstance = {
        init: initMap,
        getMap: () => map
    };

})();