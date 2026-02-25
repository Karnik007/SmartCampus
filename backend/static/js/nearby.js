/**
 * SmartCampus AI – Nearby Recommendations (Frontend)
 * Uses Geolocation API → POST /get-recommendations/ → renders cards.
 */

(function () {
  'use strict';

  // ── DOM refs ──────────────────────────────────────────────────────
  const detectBtn       = document.getElementById('detectBtn');
  const locationLabel   = document.getElementById('locationLabel');
  const locationCoords  = document.getElementById('locationCoords');
  const nearbyLoading   = document.getElementById('nearbyLoading');
  const nearbyError     = document.getElementById('nearbyError');
  const nearbyEmpty     = document.getElementById('nearbyEmpty');
  const nearbyGrid      = document.getElementById('nearbyGrid');
  const errorText       = document.getElementById('errorText');
  const retryBtn        = document.getElementById('retryBtn');
  const categoryFilters = document.getElementById('categoryFilters');
  const resultsInfo     = document.getElementById('resultsInfo');
  const resultsCount    = document.getElementById('resultsCount');

  let allResults    = [];
  let currentFilter = 'all';
  let userLat       = null;
  let userLon       = null;

  // ── Helpers ───────────────────────────────────────────────────────
  const show = el => { if (el) el.style.display = ''; };
  const hide = el => { if (el) el.style.display = 'none'; };

  const CATEGORY_ICONS = {
    restaurant: '🍽️',
    cafe:       '☕',
    market:     '🛒',
    shop:       '🛍️',
    park:       '🌳',
    game_zone:  '🎮',
    leisure:    '🏊',
    tourism:    '🗺️',
    event:      '🎉',
    place:      '📍',
    other:      '📌',
  };

  const SOURCE_COLORS = {
    OSM:        { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' },
    Foursquare: { bg: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: 'rgba(99, 102, 241, 0.3)' },
    Eventbrite: { bg: 'rgba(249, 115, 22, 0.15)', color: '#fb923c', border: 'rgba(249, 115, 22, 0.3)' },
  };

  // ── Geolocation ───────────────────────────────────────────────────
  function requestLocation() {
    if (!navigator.geolocation) {
      showError('Geolocation is not supported by your browser.');
      return;
    }

    locationLabel.textContent = 'Detecting location…';
    detectBtn.disabled = true;
    detectBtn.innerHTML = `<div class="nearby-btn-spinner"></div><span>Detecting…</span>`;

    navigator.geolocation.getCurrentPosition(onLocationSuccess, onLocationError, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 60000,
    });
  }

  function onLocationSuccess(pos) {
    userLat = pos.coords.latitude;
    userLon = pos.coords.longitude;

    locationLabel.textContent = 'Location detected ✓';
    locationCoords.textContent = `${userLat.toFixed(4)}, ${userLon.toFixed(4)}`;
    detectBtn.disabled = false;
    detectBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
      <span>Refresh Location</span>`;

    fetchRecommendations();
  }

  function onLocationError(err) {
    detectBtn.disabled = false;
    detectBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
      <span>Detect My Location</span>`;

    const msgs = {
      1: 'Location access denied. Please allow location permission.',
      2: 'Unable to determine your location. Check your network.',
      3: 'Location request timed out. Please try again.',
    };
    showError(msgs[err.code] || 'Could not get your location.');
  }

  // ── Fetch recommendations ─────────────────────────────────────────
  async function fetchRecommendations() {
    hide(nearbyError);
    hide(nearbyEmpty);
    hide(categoryFilters);
    hide(resultsInfo);
    nearbyGrid.innerHTML = '';
    show(nearbyLoading);

    try {
      const resp = await fetch('/get-recommendations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: userLat,
          longitude: userLon,
          preferences: getSelectedPreferences(),
        }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `Server error (${resp.status})`);
      }

      const data = await resp.json();
      hide(nearbyLoading);

      if (!Array.isArray(data) || data.length === 0) {
        show(nearbyEmpty);
        return;
      }

      allResults    = data;
      currentFilter = 'all';
      show(categoryFilters);
      renderCards(allResults);

    } catch (e) {
      hide(nearbyLoading);
      showError(e.message || 'Failed to load recommendations.');
    }
  }

  function getSelectedPreferences() {
    // Read active filter pills (excluding 'all')
    const pills = document.querySelectorAll('.nearby-filter-pill.active');
    const prefs = [];
    pills.forEach(p => {
      const cat = p.dataset.cat;
      if (cat && cat !== 'all') prefs.push(cat);
    });
    return prefs.length ? prefs : ['restaurant', 'cafe', 'park', 'event', 'market', 'game_zone'];
  }

  // ── Render cards ──────────────────────────────────────────────────
  function renderCards(items) {
    nearbyGrid.innerHTML = '';
    hide(nearbyEmpty);

    const filtered = currentFilter === 'all'
      ? items
      : items.filter(i => i.category === currentFilter);

    if (filtered.length === 0) {
      show(nearbyEmpty);
      hide(resultsInfo);
      return;
    }

    show(resultsInfo);
    resultsCount.textContent = `Showing ${filtered.length} recommendation${filtered.length > 1 ? 's' : ''}`;

    filtered.forEach((item, idx) => {
      const card = createCard(item, idx);
      nearbyGrid.appendChild(card);
    });
  }

  function createCard(item, index) {
    const card = document.createElement('div');
    card.className = 'nearby-card';
    card.style.animationDelay = `${index * 0.06}s`;

    const icon    = CATEGORY_ICONS[item.category] || CATEGORY_ICONS.other;
    const srcStyle = SOURCE_COLORS[item.source] || SOURCE_COLORS.OSM;
    const rating  = item.rating != null ? `${parseFloat(item.rating).toFixed(1)} ★` : 'N/A';
    const dist    = item.distance_km != null ? `${item.distance_km} km` : '—';
    const scoreDisplay = item.score != null ? item.score.toFixed(1) : '—';

    // Score colour
    let scoreClass = 'score-neutral';
    if (item.score > 3) scoreClass = 'score-high';
    else if (item.score > 0) scoreClass = 'score-mid';
    else if (item.score <= 0) scoreClass = 'score-low';

    card.innerHTML = `
      <div class="nearby-card-header">
        <span class="nearby-card-icon">${icon}</span>
        <span class="nearby-card-source" style="background:${srcStyle.bg};color:${srcStyle.color};border-color:${srcStyle.border}">
          ${item.source}
        </span>
      </div>
      <h3 class="nearby-card-name">${escapeHtml(item.name)}</h3>
      <span class="nearby-card-category">${capitalize(item.category.replace('_', ' '))}</span>
      <div class="nearby-card-meta">
        <div class="nearby-meta-item">
          <span class="nearby-meta-label">Rating</span>
          <span class="nearby-meta-value">${rating}</span>
        </div>
        <div class="nearby-meta-item">
          <span class="nearby-meta-label">Distance</span>
          <span class="nearby-meta-value">${dist}</span>
        </div>
        <div class="nearby-meta-item">
          <span class="nearby-meta-label">Score</span>
          <span class="nearby-meta-value ${scoreClass}">${scoreDisplay}</span>
        </div>
      </div>
      <div class="nearby-card-why">
        <span class="nearby-why-label">Why Recommended</span>
        <p class="nearby-why-text">${escapeHtml(item.why_recommended || '')}</p>
      </div>
    `;

    return card;
  }

  // ── Category filters ──────────────────────────────────────────────
  if (categoryFilters) {
    categoryFilters.addEventListener('click', e => {
      const pill = e.target.closest('.nearby-filter-pill');
      if (!pill) return;

      document.querySelectorAll('.nearby-filter-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentFilter = pill.dataset.cat;
      renderCards(allResults);
    });
  }

  // ── Error helpers ─────────────────────────────────────────────────
  function showError(msg) {
    hide(nearbyLoading);
    hide(nearbyEmpty);
    errorText.textContent = msg;
    show(nearbyError);
  }

  // ── Utilities ─────────────────────────────────────────────────────
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  // ── Event bindings ────────────────────────────────────────────────
  detectBtn.addEventListener('click', requestLocation);
  retryBtn.addEventListener('click', () => {
    if (userLat && userLon) fetchRecommendations();
    else requestLocation();
  });

  // Auto-detect on page load
  requestLocation();

})();
