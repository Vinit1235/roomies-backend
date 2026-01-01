const budgetSlider = document.getElementById("budgetSlider");
const budgetValue = document.getElementById("budgetValue");
const roomsGrid = document.getElementById("roomsGrid");
const findmatesGrid = document.getElementById("findmatesGrid");
const includeUnverified = document.getElementById("includeUnverified");
const filterFindmatesToggle = document.getElementById("filterFindmates");
const searchForm = document.getElementById("searchForm");
const propertyTypeFilter = document.getElementById("propertyTypeFilter");
const sortFilter = document.getElementById("sortFilter");
const searchInput = document.getElementById("searchInput");
const clearFiltersBtn = document.getElementById("clearFilters");
const searchSummary = document.getElementById("searchSummary");
const refreshFindmatesBtn = document.getElementById("refreshFindmates");
const recenterMapBtn = document.getElementById("recenterMap");
const ownerListingForm = document.getElementById("ownerListingForm");
const ownerListingFeedback = document.getElementById("ownerListingFeedback");
const contactForm = document.getElementById("contactForm");
const contactFeedback = document.getElementById("contactFeedback");

// Sidebar toggle
const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const mainContent = document.getElementById("mainContent");
const globalSearch = document.getElementById("globalSearch");

let mapInstance;
let mapMarkers;
let lastRoomsResponse = { rooms: [], meta: { total: 0 } };

// Toggle sidebar
if (menuToggle && sidebar && mainContent) {
    menuToggle.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
        mainContent.classList.toggle("expanded");

        // For mobile, use 'show' class instead
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle("show");
        }
    });

    // Close sidebar when clicking outside on mobile
    if (window.innerWidth <= 768) {
        document.addEventListener("click", (e) => {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target) && sidebar.classList.contains("show")) {
                sidebar.classList.remove("show");
            }
        });
    }
}

// Handle window resize for sidebar
let resizeTimer;
window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (window.innerWidth > 768 && sidebar) {
            sidebar.classList.remove("show");
            sidebar.classList.remove("collapsed");
        } else if (window.innerWidth <= 768 && sidebar) {
            sidebar.classList.add("collapsed");
            sidebar.classList.remove("show");
        }
    }, 250);
});

// Sync global search with main search
if (globalSearch && searchInput) {
    globalSearch.addEventListener("input", (e) => {
        searchInput.value = e.target.value;
    });

    globalSearch.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            executeSearch();
        }
    });
}

// Sidebar active state
const sidebarItems = document.querySelectorAll(".sidebar-item");
sidebarItems.forEach(item => {
    item.addEventListener("click", function () {
        // Auto-close mobile sidebar after clicking a link
        if (window.innerWidth <= 768 && sidebar) {
            sidebar.classList.remove("show");
            sidebar.classList.add("collapsed");
        }
    });
});

// Search button handler for explore page
const searchBtn = document.getElementById("searchBtn");
if (searchBtn) {
    searchBtn.addEventListener("click", () => {
        executeSearch();
    });
}

const formatCurrency = (value) =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    }).format(Number(value || 0));

const formatCapacity = (room) => {
    const total = room.capacity_total ?? 0;
    const occupied = room.capacity_occupied ?? 0;
    const slots = room.available_slots ?? Math.max(total - occupied, 0);
    return `${occupied}/${total} occupied · ${slots} open`;
};

const updateBudgetLabel = () => {
    if (budgetSlider && budgetValue) {
        budgetValue.textContent = formatCurrency(budgetSlider.value);
    }
};

const setFeedback = (node, message, variant = "") => {
    if (!node) return;
    node.textContent = message || "";
    node.dataset.variant = variant;
    node.hidden = !message;
};

const buildRoomCard = (room) => {
    const amenities = (room.amenities || []).slice(0, 4).join(" • ") || "Amenities coming soon";
    const ownerLine = room.owner ? `Managed by ${room.owner.name}` : "Owner verification pending";
    const badge = room.verified ? '<span class="badge">Verified</span>' : "";
    const capacityLine = formatCapacity(room);
    return `
        <article class="room-card" data-room-id="${room.id}">
            <div class="room-image" style="background-image: url('${room.image_url}')"></div>
            <div class="room-body">
                <header class="room-header">
                    <div>
                        <h3>${room.title}</h3>
                        <p class="room-location">${room.location} • ${room.college}</p>
                    </div>
                    <div class="room-pricing">
                        <span class="price-tag">${formatCurrency(room.price)}</span>
                        ${badge}
                    </div>
                </header>
                <div class="room-meta">
                    <span>${amenities}</span>
                    <span>${ownerLine}</span>
                    <span>${capacityLine}</span>
                </div>
            </div>
        </article>
    `;
};

const renderRooms = (rooms, target) => {
    if (!target) return;
    if (!rooms.length) {
        target.innerHTML = '<div class="empty-state">No listings match your filters right now. Try widening the criteria.</div>';
        return;
    }
    target.innerHTML = rooms.map((room) => buildRoomCard(room)).join("");
};

const plotRoomsOnMap = (rooms) => {
    if (!mapInstance || !mapMarkers) return;

    // Clear existing markers
    mapMarkers.forEach(marker => marker.setMap(null));
    mapMarkers = [];

    const bounds = new google.maps.LatLngBounds();
    rooms.forEach((room) => {
        if (room.latitude && room.longitude) {
            const position = { lat: room.latitude, lng: room.longitude };
            const marker = new google.maps.Marker({
                position: position,
                map: mapInstance,
                title: room.title,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 0C9 0 4 5 4 12c0 9 12 20 12 20s12-11 12-20c0-7-5-12-12-12z" fill="#dc2626"/>
                            <circle cx="16" cy="12" r="5" fill="white"/>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(32, 32),
                    anchor: new google.maps.Point(16, 32)
                }
            });

            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div style="padding: 8px; min-width: 180px;">
                        <strong>${room.title}</strong><br>
                        ${room.location}<br>
                        ${formatCurrency(room.price)} · ${formatCapacity(room)}
                    </div>
                `
            });

            marker.addListener('click', () => {
                infoWindow.open(mapInstance, marker);
            });

            mapMarkers.push(marker);
            bounds.extend(position);
        }
    });

    if (mapMarkers.length > 0) {
        mapInstance.fitBounds(bounds);
    }
};

// Google Maps initialization function (called by API callback)
window.initIndexMap = function () {
    const mapContainer = document.getElementById("mapView");
    if (!mapContainer) {
        console.log("[Map] Map container not found on this page");
        return;
    }

    // Skip if on explore.html (it has its own map initialization)
    if (window.isExplorePage) {
        console.log("[Map] Skipping main map initialization on explore page.");
        return;
    }

    try {
        console.log("[Map] Initializing Google Maps...");

        // Initialize Google Map centered on Mumbai
        mapInstance = new google.maps.Map(mapContainer, {
            center: { lat: 19.076, lng: 72.8777 },
            zoom: 12,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: true,
            styles: [
                {
                    featureType: "poi",
                    elementType: "labels",
                    stylers: [{ visibility: "off" }]
                }
            ]
        });

        console.log("[Map] Google Map initialized successfully");

        // Initialize markers array
        mapMarkers = [];

        // Add sample markers for demonstration
        addSampleMarkers();

        // Request user's location
        if (navigator.geolocation) {
            console.log("[Map] Requesting GPS location...");
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLat = position.coords.latitude;
                    const userLng = position.coords.longitude;
                    console.log(`[Map] User location: ${userLat}, ${userLng}`);

                    // Add user location marker with custom blue icon
                    const userMarker = new google.maps.Marker({
                        position: { lat: userLat, lng: userLng },
                        map: mapInstance,
                        title: 'Your Location',
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 10,
                            fillColor: '#3b82f6',
                            fillOpacity: 1,
                            strokeColor: '#ffffff',
                            strokeWeight: 3
                        }
                    });

                    const infoWindow = new google.maps.InfoWindow({
                        content: '<strong>📍 Your Location</strong><br>You are here'
                    });
                    infoWindow.open(mapInstance, userMarker);

                    mapInstance.setCenter({ lat: userLat, lng: userLng });
                    mapInstance.setZoom(13);
                },
                (error) => {
                    console.warn("[Map] Location access denied:", error.message);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        } else {
            console.warn("[Map] Geolocation not supported by browser");
        }
    } catch (error) {
        console.error("[Map] Error initializing map:", error);
    }
};

const addSampleMarkers = () => {
    if (!mapInstance) return;

    const sampleLocations = [
        { lat: 19.0760, lng: 72.8777, title: "Andheri East PG", price: "₹8,500" },
        { lat: 19.1136, lng: 72.8697, title: "Malad West Hostel", price: "₹6,000" },
        { lat: 19.0330, lng: 72.8569, title: "Bandra Apartment", price: "₹12,000" },
        { lat: 19.0596, lng: 72.8295, title: "Juhu Beach Studio", price: "₹15,000" },
        { lat: 19.1197, lng: 72.9080, title: "Powai Lake View", price: "₹10,500" },
    ];

    sampleLocations.forEach(loc => {
        const marker = new google.maps.Marker({
            position: { lat: loc.lat, lng: loc.lng },
            map: mapInstance,
            title: loc.title,
            icon: {
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 0C9 0 4 5 4 12c0 9 12 20 12 20s12-11 12-20c0-7-5-12-12-12z" fill="#dc2626"/>
                        <circle cx="16" cy="12" r="5" fill="white"/>
                    </svg>
                `),
                scaledSize: new google.maps.Size(32, 32),
                anchor: new google.maps.Point(16, 32)
            }
        });

        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div style="padding: 8px;">
                    <strong>${loc.title}</strong><br>
                    ${loc.price}/month<br>
                    <a href="/explore">View Details</a>
                </div>
            `
        });

        marker.addListener('click', () => {
            infoWindow.open(mapInstance, marker);
        });

        if (!mapMarkers) mapMarkers = [];
        mapMarkers.push(marker);
    });
};

const fetchRooms = async (params = {}) => {
    const url = new URL("/api/rooms", window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
            url.searchParams.set(key, value);
        }
    });
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Unable to fetch rooms");
    }
    return response.json();
};

const executeSearch = async () => {
    if (!roomsGrid) return;

    // Smooth scroll to results if not auto-loading
    if (searchInput && (searchInput.value || propertyTypeFilter.value)) {
        document.getElementById("roomsExplorer").scrollIntoView({ behavior: 'smooth' });
    }

    roomsGrid.dataset.loading = "true";
    setFeedback(searchSummary, "Fetching live availability…", "info");

    try {
        const params = {
            limit: 24,
            q: searchInput?.value || "",
            property_type: propertyTypeFilter?.value || "",
            max_rent: budgetSlider ? budgetSlider.value : undefined,
            sort: sortFilter?.value || "price_asc",
            include_unverified: includeUnverified?.checked ? 1 : 0,
            min_available: filterFindmatesToggle?.checked ? 1 : undefined,
        };

        const result = await fetchRooms(params);
        lastRoomsResponse = result;

        renderRooms(result.rooms || [], roomsGrid);
        plotRoomsOnMap(result.rooms || []);

        const meta = result.meta || {};
        const summaryBits = [
            meta.total ? `${meta.total} total matches` : null,
            params.max_rent ? `Budget ≤ ${formatCurrency(params.max_rent)}` : null,
            params.property_type ? `Type: ${params.property_type}` : null,
            params.min_available ? `Findmates enabled` : null,
        ].filter(Boolean);
        setFeedback(searchSummary, summaryBits.join(" · "), "info");
    } catch (error) {
        console.error(error);
        renderRooms([], roomsGrid);
        setFeedback(searchSummary, "We could not load listings. Please try again in a moment.", "error");
    } finally {
        roomsGrid.dataset.loading = "false";
    }
};

const loadFindmates = async () => {
    if (!findmatesGrid) return;
    findmatesGrid.dataset.loading = "true";

    try {
        const result = await fetchRooms({
            min_available: 1,
            sort: "slots_desc",
            limit: 6,
        });
        renderRooms(result.rooms || [], findmatesGrid);
    } catch (error) {
        console.error(error);
        renderRooms([], findmatesGrid);
    } finally {
        findmatesGrid.dataset.loading = "false";
    }
};

const handleOwnerListingSubmit = async (event) => {
    event.preventDefault();
    if (!ownerListingForm) return;

    const formData = new FormData(ownerListingForm);
    const payload = Object.fromEntries(formData.entries());
    setFeedback(ownerListingFeedback, "Submitting listing…", "info");

    try {
        const response = await fetch("/api/owner/listings", {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(payload),
        });

        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        if (response.status === 401 || response.status === 403) {
            setFeedback(ownerListingFeedback, "Please sign in as an owner to publish listings.", "error");
            return;
        }

        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(body.error || "Unable to create listing");
        }

        await response.json();
        setFeedback(ownerListingFeedback, "Listing submitted for verification. We will notify you once it is live.", "success");
        ownerListingForm.reset();
        executeSearch();
        loadFindmates();
    } catch (error) {
        console.error(error);
        setFeedback(ownerListingFeedback, error.message || "Could not submit listing.", "error");
    }
};

const handleContactSubmit = async (event) => {
    event.preventDefault();
    if (!contactForm) return;

    const formData = new FormData(contactForm);
    const payload = Object.fromEntries(formData.entries());
    setFeedback(contactFeedback, "Sending…", "info");

    try {
        const response = await fetch("/contact", {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(payload),
        });

        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(body.error || "Unable to send message");
        }

        setFeedback(contactFeedback, "Thanks! Our partnerships team will get back shortly.", "success");
        contactForm.reset();
    } catch (error) {
        console.error(error);
        setFeedback(contactFeedback, error.message || "Could not send message.", "error");
    }
};

if (budgetSlider) {
    budgetSlider.addEventListener("input", updateBudgetLabel);
    updateBudgetLabel();
}

if (searchForm) {
    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        executeSearch();
    });
}

if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        if (propertyTypeFilter) propertyTypeFilter.value = "";
        if (sortFilter) sortFilter.value = "price_asc";
        if (includeUnverified) includeUnverified.checked = false;
        if (filterFindmatesToggle) filterFindmatesToggle.checked = true;
        if (budgetSlider) {
            budgetSlider.value = 12000;
            updateBudgetLabel();
        }
        executeSearch();
    });
}

if (includeUnverified) {
    includeUnverified.addEventListener("change", executeSearch);
}

if (filterFindmatesToggle) {
    filterFindmatesToggle.addEventListener("change", executeSearch);
}

if (refreshFindmatesBtn) {
    refreshFindmatesBtn.addEventListener("click", loadFindmates);
}

if (recenterMapBtn) {
    recenterMapBtn.addEventListener("click", () => {
        plotRoomsOnMap(lastRoomsResponse.rooms || []);
    });
}

if (ownerListingForm) {
    ownerListingForm.addEventListener("submit", handleOwnerListingSubmit);
}

if (contactForm) {
    contactForm.addEventListener("submit", handleContactSubmit);
}

window.addEventListener("DOMContentLoaded", () => {
    // Map initialization is handled by Google Maps callback (initIndexMap)
    // Skip manual initialization as Google Maps API calls the callback
    initVoiceSearch();
    initPWA();
    loadFlashDeals();
    executeSearch(); // Auto-load listings on page load
});


// ============= VOICE SEARCH =============

function initVoiceSearch() {
    const voiceBtn = document.getElementById("voiceSearchBtn");
    if (!voiceBtn) return;

    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        voiceBtn.style.display = "none";
        console.warn("[Voice] Speech Recognition not supported");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";

    let isListening = false;

    voiceBtn.addEventListener("click", () => {
        if (isListening) {
            recognition.stop();
            return;
        }

        recognition.start();
        isListening = true;
        voiceBtn.classList.add("listening");
        voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("[Voice] Transcript:", transcript);

        // Update search input
        if (searchInput) {
            searchInput.value = transcript;
        }
        if (globalSearch) {
            globalSearch.value = transcript;
        }

        // Auto-execute search
        executeSearch();
    };

    recognition.onerror = (event) => {
        console.error("[Voice] Recognition error:", event.error);
        isListening = false;
        voiceBtn.classList.remove("listening");
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };

    recognition.onend = () => {
        isListening = false;
        voiceBtn.classList.remove("listening");
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };
}


// ============= PWA SUPPORT =============

function initPWA() {
    // Register service worker
    if ("serviceWorker" in navigator) {
        navigator.serviceWorker
            .register("/static/service-worker.js")
            .then((registration) => {
                console.log("[PWA] Service Worker registered:", registration.scope);
            })
            .catch((error) => {
                console.error("[PWA] Service Worker registration failed:", error);
            });
    }

    // Install prompt
    let deferredPrompt;
    window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        deferredPrompt = e;

        // Show install button (if exists)
        const installBtn = document.getElementById("pwaInstallBtn");
        if (installBtn) {
            installBtn.style.display = "block";
            installBtn.addEventListener("click", () => {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    console.log("[PWA] User choice:", choiceResult.outcome);
                    deferredPrompt = null;
                    installBtn.style.display = "none";
                });
            });
        }
    });
}


// ============= FLASH DEALS =============

function loadFlashDeals() {
    fetch("/api/flash-deals")
        .then((res) => res.json())
        .then((data) => {
            console.log("[Flash Deals] Loaded:", data.count);
            if (data.deals && data.deals.length > 0) {
                displayFlashDealsOnMap(data.deals);
            }
        })
        .catch((err) => console.error("[Flash Deals] Error:", err));
}

function displayFlashDealsOnMap(deals) {
    if (!mapInstance || !deals.length) return;

    deals.forEach((deal) => {
        // Find room data
        fetch(`/api/rooms?room_id=${deal.room_id}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.rooms && data.rooms.length > 0) {
                    const room = data.rooms[0];
                    if (room.latitude && room.longitude) {
                        // Create flash deal marker with bold icon
                        const marker = new google.maps.Marker({
                            position: { lat: room.latitude, lng: room.longitude },
                            map: mapInstance,
                            title: '⚡ Flash Deal: ' + room.title,
                            icon: {
                                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                                    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                                        <circle cx="20" cy="20" r="18" fill="#fbbf24" stroke="#f59e0b" stroke-width="2"/>
                                        <text x="20" y="26" text-anchor="middle" font-size="18" fill="#1f2937">⚡</text>
                                    </svg>
                                `),
                                scaledSize: new google.maps.Size(40, 40),
                                anchor: new google.maps.Point(20, 20)
                            },
                            animation: google.maps.Animation.BOUNCE
                        });

                        // Stop bouncing after 2 seconds
                        setTimeout(() => {
                            marker.setAnimation(null);
                        }, 2000);

                        const infoWindow = new google.maps.InfoWindow({
                            content: `
                                <div style="padding: 12px; min-width: 200px;">
                                    <h4 style="margin: 0 0 8px 0; color: #f59e0b;">⚡ FLASH DEAL ⚡</h4>
                                    <p style="margin: 0 0 4px 0;"><strong>${room.title}</strong></p>
                                    <p style="margin: 0 0 4px 0;">
                                        <del style="color: #9ca3af;">₹${deal.original_price}</del>
                                        <span style="color: #dc2626; font-weight: bold; font-size: 18px;"> ₹${deal.deal_price}</span>
                                    </p>
                                    <p style="margin: 0 0 4px 0; color: #16a34a; font-weight: bold;">${deal.discount_percent}% OFF</p>
                                    <p style="margin: 0; color: #64748b;">⏰ ${Math.floor(deal.time_remaining_hours)}h remaining</p>
                                </div>
                            `
                        });

                        marker.addListener('click', () => {
                            infoWindow.open(mapInstance, marker);
                        });
                    }
                }
            });
    });
}


// ============= CARBON SAVINGS CALCULATOR =============

function calculateCarbonSavings(roomType) {
    // Estimated CO2 savings (kg/month) by choosing shared vs individual
    const carbonData = {
        shared: { electricity: 30, water: 15, transport: 25 }, // Lower due to shared resources
        individual: { electricity: 80, water: 40, transport: 50 }, // Higher individual consumption
    };

    const shared = carbonData.shared;
    const individual = carbonData.individual;

    const savings = {
        electricity: individual.electricity - shared.electricity,
        water: individual.water - shared.water,
        transport: individual.transport - shared.transport,
        total: 0,
    };

    savings.total = savings.electricity + savings.water + savings.transport;

    return savings;
}

function displayCarbonSavings(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const savings = calculateCarbonSavings("shared");

    container.innerHTML = `
        <div class="carbon-calculator">
            <h3>🌱 Environmental Impact</h3>
            <p>By choosing shared housing, you save approximately:</p>
            <ul>
                <li><strong>${savings.total} kg CO₂/month</strong></li>
                <li>Electricity: ${savings.electricity} kg CO₂</li>
                <li>Water: ${savings.water} kg CO₂</li>
                <li>Transport: ${savings.transport} kg CO₂</li>
            </ul>
            <p class="carbon-message">That's like planting ${Math.floor(savings.total / 10)} trees every month! 🌳</p>
        </div>
    `;
}

// ============= AUTOCOMPLETE SEARCH =============

const suggestionsContainer = document.getElementById("searchSuggestions");
let debounceTimer;

if (searchInput && suggestionsContainer) {
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);

        if (query.length < 2) {
            suggestionsContainer.classList.remove("active");
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
                const suggestions = await res.json();

                if (suggestions.length > 0) {
                    suggestionsContainer.innerHTML = suggestions.map(s => `
                        <div class="suggestion-item" onclick="selectSuggestion('${s.text.replace(/'/g, "\\'")}')">
                            <span class="suggestion-text">${s.text}</span>
                            <span class="suggestion-type">${s.type}</span>
                        </div>
                     `).join("");
                    suggestionsContainer.classList.add("active");
                } else {
                    suggestionsContainer.classList.remove("active");
                }
            } catch (err) {
                console.error(err);
            }
        }, 300);
    });

    // Hide when clicking outside
    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.classList.remove("active");
        }
    });
}

window.selectSuggestion = (text) => {
    if (searchInput) {
        searchInput.value = text;
        if (suggestionsContainer) suggestionsContainer.classList.remove("active");
        executeSearch();
    }
};
