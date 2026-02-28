/* ===================================================
   SmartCampus AI – Dashboard Page Logic
   Form handling, slider live values, submit + redirect
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Note: Django's @login_required handles auth server-side

    // Init shared components (navbar, theme)
    initShared();

    // ---- Slider live values ----
    const budgetSlider = document.getElementById('budgetSlider');
    const budgetValue = document.getElementById('budgetValue');
    budgetSlider.addEventListener('input', () => {
        budgetValue.textContent = `₹${budgetSlider.value}`;
    });

    const weightSliders = [
        { input: 'weightPrice', output: 'weightPriceVal' },
        { input: 'weightRating', output: 'weightRatingVal' },
        { input: 'weightDistance', output: 'weightDistanceVal' }
    ];

    weightSliders.forEach(({ input, output }) => {
        const slider = document.getElementById(input);
        const display = document.getElementById(output);
        slider.addEventListener('input', () => {
            display.textContent = `${slider.value}%`;
        });
    });

    // ---- Detect Location ----
    const CAMPUS_COORDS = {
        main: { lat: 28.6139, lng: 77.2090, label: 'Main Campus' },
        engineering: { lat: 28.6150, lng: 77.2100, label: 'Engineering Block' },
        north: { lat: 28.6160, lng: 77.2080, label: 'North Block' },
        sports: { lat: 28.6170, lng: 77.2110, label: 'Sports Complex' },
    };

    function haversineKm(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2;
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    function findNearestCampus(lat, lng) {
        let nearest = null, minDist = Infinity;
        for (const [key, c] of Object.entries(CAMPUS_COORDS)) {
            const d = haversineKm(lat, lng, c.lat, c.lng);
            if (d < minDist) { minDist = d; nearest = { key, ...c, distance: d }; }
        }
        return nearest;
    }

    const detectBtn = document.getElementById('detectLocationBtn');
    const locationStatus = document.getElementById('locationStatus');
    const locationSelect = document.getElementById('locationPref');

    detectBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            showLocationStatus('Geolocation is not supported by your browser.', 'error');
            return;
        }

        // Show loading state
        detectBtn.classList.add('detecting');
        detectBtn.querySelector('.detect-icon').style.display = 'none';
        detectBtn.querySelector('.detect-text').textContent = 'Detecting…';
        detectBtn.querySelector('.detect-spinner').style.display = 'block';
        detectBtn.disabled = true;
        showLocationStatus('Requesting location access…', 'info');

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;

                // Show coordinates
                showLocationStatus(`📍 Your location: ${latitude.toFixed(4)}°N, ${longitude.toFixed(4)}°E`, 'success');
                resetDetectBtn();
            },
            (error) => {
                let msg = 'Could not detect location.';
                if (error.code === 1) msg = 'Location access denied. Please allow it in your browser.';
                else if (error.code === 2) msg = 'Location unavailable. Try again.';
                else if (error.code === 3) msg = 'Location request timed out.';
                showLocationStatus(msg, 'error');
                resetDetectBtn();
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    });

    function showLocationStatus(msg, type) {
        locationStatus.textContent = msg;
        locationStatus.className = 'location-status';
        if (type) locationStatus.classList.add(`location-status--${type}`);
    }

    function resetDetectBtn() {
        detectBtn.classList.remove('detecting');
        detectBtn.querySelector('.detect-icon').style.display = '';
        detectBtn.querySelector('.detect-text').textContent = 'Detect';
        detectBtn.querySelector('.detect-spinner').style.display = 'none';
        detectBtn.disabled = false;
    }

    // ---- Restore previous preferences if any ----
    const saved = sessionStorage.getItem('smartcampus-prefs');
    if (saved) {
        try {
            const prefs = JSON.parse(saved);
            budgetSlider.value = prefs.budget;
            budgetValue.textContent = `₹${prefs.budget}`;
            document.getElementById('dietaryPref').value = prefs.dietary;
            document.getElementById('locationPref').value = prefs.location;
            document.getElementById('availableTime').value = prefs.availableTime;
            document.getElementById('weightPrice').value = prefs.weightPrice;
            document.getElementById('weightPriceVal').textContent = `${prefs.weightPrice}%`;
            document.getElementById('weightRating').value = prefs.weightRating;
            document.getElementById('weightRatingVal').textContent = `${prefs.weightRating}%`;
            document.getElementById('weightDistance').value = prefs.weightDistance;
            document.getElementById('weightDistanceVal').textContent = `${prefs.weightDistance}%`;

            // Restore checkboxes
            const boxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
            boxes.forEach(cb => {
                cb.checked = (prefs.interests || []).includes(cb.value);
            });
        } catch { /* ignore corrupt data */ }
    }

    // ---- Form submission ----
    document.getElementById('preferencesForm').addEventListener('submit', (e) => {
        e.preventDefault();

        const prefs = {
            budget: parseInt(budgetSlider.value),
            dietary: document.getElementById('dietaryPref').value,
            location: document.getElementById('locationPref').value,
            availableTime: parseInt(document.getElementById('availableTime').value),
            interests: Array.from(document.querySelectorAll('.checkbox-group input:checked')).map(cb => cb.value),
            weightPrice: parseInt(document.getElementById('weightPrice').value),
            weightRating: parseInt(document.getElementById('weightRating').value),
            weightDistance: parseInt(document.getElementById('weightDistance').value)
        };

        // Save to sessionStorage and navigate to results
        sessionStorage.setItem('smartcampus-prefs', JSON.stringify(prefs));
        window.location.href = '/results/';
    });
});
