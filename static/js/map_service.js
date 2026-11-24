// Live Leaflet.js Map & Verified Petrol Pump Locator

document.addEventListener('DOMContentLoaded', () => {
    const mapElem = document.getElementById('leaflet-map');
    if (!mapElem) return;

    // Center coordinates (monitored urban grid)
    const defaultCenter = [19.0760, 72.8777];
    const map = L.map('leaflet-map').setView(defaultCenter, 13);

    // OpenStreetMap Dark / Standard Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors | AI Smart Traffic Analyzer',
        maxZoom: 19
    }).addTo(map);

    // Custom Icons
    const cameraIcon = L.divIcon({
        className: 'custom-map-icon camera-pin',
        html: '<div style="background:#a855f7; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; border:2px solid #fff; box-shadow:0 0 14px #a855f7;"><i class="bi bi-camera-video-fill"></i></div>',
        iconSize: [34, 34],
        iconAnchor: [17, 17]
    });

    const pumpIcon = L.divIcon({
        className: 'custom-map-icon pump-pin',
        html: '<div style="background:#06b6d4; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; border:2px solid #fff; box-shadow:0 0 14px #06b6d4;"><i class="bi bi-fuel-pump-fill"></i></div>',
        iconSize: [34, 34],
        iconAnchor: [17, 17]
    });

    const userIcon = L.divIcon({
        className: 'custom-map-icon user-pin',
        html: '<div style="background:#10b981; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; border:2px solid #fff; box-shadow:0 0 18px #10b981;"><i class="bi bi-geo-alt-fill"></i></div>',
        iconSize: [36, 36],
        iconAnchor: [18, 18]
    });

    // 1. Add Configured Camera Markers
    if (window.MAP_CAMERAS && Array.isArray(window.MAP_CAMERAS)) {
        window.MAP_CAMERAS.forEach(cam => {
            if (cam.latitude && cam.longitude) {
                const marker = L.marker([cam.latitude, cam.longitude], { icon: cameraIcon }).addTo(map);
                const popupContent = `
                    <div style="color:#0f172a; font-family:sans-serif; min-width:200px;">
                        <h6 style="margin:0 0 4px; color:#6b21a8; font-weight:700;">${cam.camera_id}: ${cam.name}</h6>
                        <p style="margin:0 0 6px; font-size:12px; color:#475569;">${cam.location}</p>
                        <span class="badge bg-purple" style="background:#7e22ce; color:#fff; padding:3px 8px; font-size:11px;">Status: ${cam.status}</span>
                        <div style="margin-top:8px;">
                            <a href="/cameras/${cam.camera_id}/" class="btn btn-sm" style="background:#9333ea; color:#fff; font-size:11px; padding:3px 10px; text-decoration:none; border-radius:4px;">Open Live Stream</a>
                        </div>
                    </div>
                `;
                marker.bindPopup(popupContent);
            }
        });
    }

    // 2. Add Petrol Pump Markers
    if (window.PETROL_PUMPS && Array.isArray(window.PETROL_PUMPS)) {
        window.PETROL_PUMPS.forEach(pump => {
            const marker = L.marker([pump.latitude, pump.longitude], { icon: pumpIcon }).addTo(map);
            const fuelsList = pump.fuels.join(', ');
            const popupContent = `
                <div style="color:#0f172a; font-family:sans-serif; min-width:220px;">
                    <h6 style="margin:0 0 4px; color:#0e7490; font-weight:700;"><i class="bi bi-fuel-pump"></i> ${pump.name}</h6>
                    <p style="margin:0 0 4px; font-size:12px; color:#334155;"><strong>Address:</strong> ${pump.address}</p>
                    <p style="margin:0 0 4px; font-size:11px; color:#475569;"><strong>Fuels:</strong> ${fuelsList}</p>
                    <p style="margin:0 0 8px; font-size:11px; color:#047857;"><strong>Hours:</strong> ${pump.operating_hours}</p>
                    <a href="https://www.google.com/maps/dir/?api=1&destination=${pump.latitude},${pump.longitude}" target="_blank" class="btn btn-sm" style="background:#0891b2; color:#fff; font-size:11px; padding:3px 10px; text-decoration:none; border-radius:4px;">Get Directions</a>
                </div>
            `;
            marker.bindPopup(popupContent);
        });
    }

    // 3. User Geolocation Permission & Nearest Petrol Pump Finder
    const locateBtn = document.getElementById('btn-find-nearest-pump');
    const geoInfoBox = document.getElementById('geo-status-info');

    if (locateBtn) {
        locateBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert('Geolocation is not supported by your browser.');
                return;
            }

            locateBtn.disabled = true;
            locateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Locating you...';

            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    locateBtn.disabled = false;
                    locateBtn.innerHTML = '<i class="bi bi-crosshair2 me-1"></i> My Location Found';

                    const uLat = pos.coords.latitude;
                    const uLng = pos.coords.longitude;

                    // Add user marker
                    const uMarker = L.marker([uLat, uLng], { icon: userIcon }).addTo(map);
                    uMarker.bindPopup('<b>You Are Here</b><br>GPS Geolocation Active').openPopup();
                    map.setView([uLat, uLng], 14);

                    // Auto-fill SOS latitude & longitude if on SOS form
                    const latInput = document.getElementById('sos-latitude');
                    const lngInput = document.getElementById('sos-longitude');
                    if (latInput && lngInput) {
                        latInput.value = uLat.toFixed(6);
                        lngInput.value = uLng.toFixed(6);
                    }

                    // Query nearest pumps API
                    try {
                        const r = await fetch(`/api/petrol-pumps/?lat=${uLat}&lng=${uLng}`);
                        const d = await r.json();
                        if (d.status === 'success' && d.petrol_pumps.length > 0) {
                            const nearest = d.petrol_pumps[0];
                            if (geoInfoBox) {
                                geoInfoBox.innerHTML = `
                                    <div class="alert alert-info py-2 px-3 mt-2" style="background:rgba(6,182,212,0.15); border-color:#06b6d4; color:#fff;">
                                        <strong><i class="bi bi-geo-fill"></i> Nearest Station:</strong> ${nearest.name} (${nearest.distance_km} km away)<br>
                                        <small>${nearest.address} &bull; ${nearest.fuels.join(', ')}</small>
                                        <div class="mt-1">
                                            <a href="https://www.google.com/maps/dir/?api=1&destination=${nearest.latitude},${nearest.longitude}" target="_blank" class="btn btn-sm btn-cyan py-0 px-2" style="font-size:11px;">Directions</a>
                                        </div>
                                    </div>
                                `;
                            }
                        }
                    } catch (err) {
                        console.error('Failed to fetch nearest pump:', err);
                    }
                },
                (err) => {
                    locateBtn.disabled = false;
                    locateBtn.innerHTML = '<i class="bi bi-crosshair2 me-1"></i> Find Nearest Petrol Pump';
                    alert(`Location error (${err.message}). Using default grid coordinates.`);
                },
                { timeout: 10000, enableHighAccuracy: true }
            );
        });
    }
});
