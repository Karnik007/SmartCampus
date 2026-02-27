/* ===================================================
   SmartCampus AI – Results Page (v6 – Precise Location)
   Strict GPS location → /get-recommendations/ with adaptive radius
   =================================================== */

(function () {
  'use strict';

  // ── DOM refs ──────────────────────────────────────────────────────
  const detectBtn = document.getElementById('detectBtn');
  const locationLabel = document.getElementById('locationLabel');
  const locationCoords = document.getElementById('locationCoords');
  const nearbyLoading = document.getElementById('nearbyLoading');
  const nearbyError = document.getElementById('nearbyError');
  const nearbyEmpty = document.getElementById('nearbyEmpty');
  const nearbyGrid = document.getElementById('nearbyGrid');
  const errorText = document.getElementById('errorText');
  const retryBtn = document.getElementById('retryBtn');
  const categoryFilters = document.getElementById('categoryFilters');
  const resultsInfo = document.getElementById('resultsInfo');
  const resultsCount = document.getElementById('resultsCount');

  let allResults = [];
  let currentFilter = 'all';
  let userLat = null;
  let userLon = null;
  let userAccuracy = null;
  let locationResolved = false;
  let watchId = null;
  let bestCandidate = null;
  const TARGET_ACCURACY_M = 120;
  const MAX_ACCEPTABLE_ACCURACY_M = 1200;

  // ── Helpers ───────────────────────────────────────────────────────
  const show = el => { if (el) el.style.display = ''; };
  const hide = el => { if (el) el.style.display = 'none'; };

  const CATEGORY_ICONS = {
    food: '🍱',
    restaurant: '🍽️',
    cafe: '☕',
    market: '🛒',
    shop: '🛍️',
    park: '🌳',
    game_zone: '🎮',
    leisure: '🏊',
    tourism: '🗺️',
    event: '🎉',
    place: '📍',
    other: '📌',
  };

  const SOURCE_COLORS = {
    OSM: { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' },
    Foursquare: { bg: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: 'rgba(99, 102, 241, 0.3)' },
    Eventbrite: { bg: 'rgba(249, 115, 22, 0.15)', color: '#fb923c', border: 'rgba(249, 115, 22, 0.3)' },
    SmartCampus: { bg: 'rgba(14, 165, 233, 0.15)', color: '#38bdf8', border: 'rgba(14, 165, 233, 0.35)' },
  };

  // ── Category matching ─────────────────────────────────────────────
  const CATEGORY_MAP = {
    food: ['food'],
    restaurant: ['restaurant', 'dining', 'food', 'fast_food', 'food_court'],
    cafe: ['cafe', 'coffee', 'tea', 'bar', 'pub', 'bakery'],
    market: ['market', 'shop', 'supermarket', 'grocery', 'marketplace', 'convenience'],
    game_zone: ['game_zone', 'game', 'arcade', 'sport', 'sports', 'playground', 'leisure', 'entertainment', 'cinema', 'bowling'],
    park: ['park', 'garden', 'nature', 'nature_reserve', 'recreation'],
    event: ['event', 'festival', 'concert', 'meetup', 'workshop', 'conference'],
  };

  function matchesCategory(itemCategory, filterCat) {
    if (filterCat === 'all') return true;
    if (!itemCategory) return false;

    const cat = itemCategory.toLowerCase().trim();
    const validMatches = CATEGORY_MAP[filterCat];

    if (!validMatches) return cat === filterCat;

    for (const m of validMatches) {
      if (cat === m || cat.includes(m) || m.includes(cat)) return true;
    }
    return false;
  }

  // ── Geolocation (Precise GPS-first) ───────────────────────────────
  function requestLocation() {
    if (!navigator.geolocation) {
      showError('Geolocation is not supported by this browser.');
      return;
    }

    locationResolved = false;
    locationLabel.textContent = 'Detecting location…';
    detectBtn.disabled = true;
    detectBtn.innerHTML = '<div class="nearby-btn-spinner"></div><span>Detecting…</span>';

    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }

    // Strategy 1: getCurrentPosition (high accuracy, no stale cache)
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        if (locationResolved) return;
        if (pos.coords.accuracy && pos.coords.accuracy > TARGET_ACCURACY_M) {
          // Ask watchPosition for a better fix.
          startWatchPosition();
          return;
        }
        onLocationFound(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy || null, 'GPS');
      },
      function (err) {
        console.warn('[SmartCampus] getCurrentPosition failed:', err.message);
        startWatchPosition();
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }

  function startWatchPosition() {
    watchId = navigator.geolocation.watchPosition(
      function (pos) {
        if (locationResolved) return;
        var acc = pos.coords.accuracy || null;
        // Save best candidate while waiting for strong GPS.
        if (bestCandidate === null || (acc && acc < bestCandidate.accuracy)) {
          bestCandidate = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: acc };
        }
        // Accept if strong enough, otherwise keep watching.
        if (!acc || acc <= TARGET_ACCURACY_M) {
          onLocationFound(pos.coords.latitude, pos.coords.longitude, acc, 'GPS');
          if (watchId !== null) { navigator.geolocation.clearWatch(watchId); watchId = null; }
        } else {
          locationLabel.textContent = 'Improving GPS accuracy…';
          locationCoords.textContent = 'Current accuracy: ±' + Math.round(acc) + 'm';
        }
      },
      function (err) {
        console.warn('[SmartCampus] watchPosition failed:', err.message);
        if (!locationResolved) {
          detectBtn.disabled = false;
          detectBtn.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><circle cx="12" cy="12" r="3"/></svg>' +
            '<span>Detect My Location</span>';
          showError('Could not get precise GPS location. Enable location permission and high accuracy mode.');
        }
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
    );

    setTimeout(function () {
      if (!locationResolved) {
        if (watchId !== null) { navigator.geolocation.clearWatch(watchId); watchId = null; }
        if (bestCandidate && (!bestCandidate.accuracy || bestCandidate.accuracy <= MAX_ACCEPTABLE_ACCURACY_M)) {
          onLocationFound(bestCandidate.lat, bestCandidate.lon, bestCandidate.accuracy, 'Approx');
          return;
        }
        detectBtn.disabled = false;
        detectBtn.innerHTML =
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><circle cx="12" cy="12" r="3"/></svg>' +
          '<span>Detect My Location</span>';
        showError('Could not get current location. Use coordinates or retry.');
      }
    }, 22000);
  }

  function onLocationFound(lat, lon, accuracy, source) {
    if (locationResolved) return;
    locationResolved = true;
    userLat = lat;
    userLon = lon;
    userAccuracy = accuracy;

    var label = 'Precise location detected ✓';
    if (source === 'Approx') label = 'Approximate location detected ✓';

    locationLabel.textContent = label;
    locationCoords.textContent = userLat.toFixed(5) + ', ' + userLon.toFixed(5) +
      (userAccuracy ? (' (±' + Math.round(userAccuracy) + 'm)') : '');
    detectBtn.disabled = false;
    detectBtn.innerHTML =
      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><circle cx="12" cy="12" r="3"/></svg>' +
      '<span>Refresh Location</span>';

    console.log('[SmartCampus] Location via ' + source + ': ' + lat.toFixed(4) + ', ' + lon.toFixed(4));
    fetchRecommendations();
  }

  // ── Fetch recommendations ─────────────────────────────────────────
  function fetchRecommendations() {
    hide(nearbyError);
    hide(nearbyEmpty);
    hide(categoryFilters);
    hide(resultsInfo);
    nearbyGrid.innerHTML = '';
    show(nearbyLoading);

    const controller = new AbortController();
    const timeoutId = setTimeout(function () { controller.abort(); }, 35000);

    fetch('/get-recommendations/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      signal: controller.signal,
      body: JSON.stringify({
        latitude: userLat,
        longitude: userLon,
        accuracy_m: userAccuracy,
        preferences: ['food', 'restaurant', 'cafe', 'park', 'event', 'market', 'game_zone'],
      }),
    })
      .then(function (resp) {
        if (!resp.ok) {
          return resp.json().catch(function () { return {}; }).then(function (d) {
            throw new Error(d.error || 'Server error (' + resp.status + ')');
          });
        }
        return resp.json();
      })
      .then(function (data) {
        clearTimeout(timeoutId);
        hide(nearbyLoading);

        console.log('[SmartCampus] API returned', data.length, 'items');

        if (!Array.isArray(data) || data.length === 0) {
          show(nearbyEmpty);
          return;
        }

        allResults = data;
        currentFilter = 'all';

        var pills = document.querySelectorAll('.nearby-filter-pill');
        pills.forEach(function (p) { p.classList.remove('active'); });
        var allPill = document.querySelector('.nearby-filter-pill[data-cat="all"]');
        if (allPill) allPill.classList.add('active');

        show(categoryFilters);
        renderCards(allResults);
      })
      .catch(function (e) {
        clearTimeout(timeoutId);
        hide(nearbyLoading);
        if (e.name === 'AbortError') {
          showError('Request timed out. Please try again.');
          return;
        }
        showError(e.message || 'Failed to load recommendations.');
      });
  }

  // ── Render cards ──────────────────────────────────────────────────
  function renderCards(items) {
    nearbyGrid.innerHTML = '';
    hide(nearbyEmpty);

    var filtered;
    if (currentFilter === 'all') {
      filtered = items;
    } else {
      filtered = [];
      for (var i = 0; i < items.length; i++) {
        if (matchesCategory(items[i].category, currentFilter)) {
          filtered.push(items[i]);
        }
      }
    }

    if (filtered.length === 0) {
      show(nearbyEmpty);
      hide(resultsInfo);
      return;
    }

    show(resultsInfo);
    resultsCount.textContent = 'Showing ' + filtered.length + ' recommendation' + (filtered.length > 1 ? 's' : '');

    for (var j = 0; j < filtered.length; j++) {
      nearbyGrid.appendChild(createCard(filtered[j], j));
    }
  }

  function createCard(item, index) {
    var card = document.createElement('div');
    card.className = 'nearby-card';
    card.style.animationDelay = (index * 0.06) + 's';

    var icon = CATEGORY_ICONS[item.category] || CATEGORY_ICONS.other;
    var srcStyle = SOURCE_COLORS[item.source] || SOURCE_COLORS.OSM;
    var rating = item.rating != null ? parseFloat(item.rating).toFixed(1) + ' ★' : 'N/A';
    var dist = item.distance_km != null ? item.distance_km + ' km' : '—';
    var scoreVal = item.score != null ? item.score : null;
    var scoreDisplay = scoreVal != null ? scoreVal.toFixed(1) : '—';
    var locationText = item.location || 'Location unavailable';
    var hasCoords = item.latitude !== null && item.latitude !== undefined && item.longitude !== null && item.longitude !== undefined;
    var mapLink = hasCoords ? ('https://www.google.com/maps?q=' + encodeURIComponent(item.latitude + ',' + item.longitude)) : '';
    var catLabel = (item.category || 'other').replace(/_/g, ' ');
    catLabel = catLabel.charAt(0).toUpperCase() + catLabel.slice(1);

    var scoreClass = 'score-neutral';
    if (scoreVal !== null) {
      if (scoreVal > 3) scoreClass = 'score-high';
      else if (scoreVal > 0) scoreClass = 'score-mid';
      else scoreClass = 'score-low';
    }

    card.innerHTML =
      '<div class="nearby-card-header">' +
      '<span class="nearby-card-icon">' + icon + '</span>' +
      '<span class="nearby-card-source" style="background:' + srcStyle.bg + ';color:' + srcStyle.color + ';border-color:' + srcStyle.border + '">' +
      item.source +
      '</span>' +
      '</div>' +
      '<h3 class="nearby-card-name">' + escapeHtml(item.name) + '</h3>' +
      '<span class="nearby-card-category">' + catLabel + '</span>' +
      '<div class="nearby-card-location">' +
      '<span class="nearby-location-dot">📍</span>' +
      '<span class="nearby-location-text">' + escapeHtml(locationText) + '</span>' +
      (hasCoords ? ('<a class="nearby-map-link" href="' + mapLink + '" target="_blank" rel="noopener">Map</a>') : '') +
      '</div>' +
      '<div class="nearby-card-meta">' +
      '<div class="nearby-meta-item"><span class="nearby-meta-label">Rating</span><span class="nearby-meta-value">' + rating + '</span></div>' +
      '<div class="nearby-meta-item"><span class="nearby-meta-label">Distance</span><span class="nearby-meta-value">' + dist + '</span></div>' +
      '<div class="nearby-meta-item"><span class="nearby-meta-label">Score</span><span class="nearby-meta-value ' + scoreClass + '">' + scoreDisplay + '</span></div>' +
      '</div>' +
      '<div class="nearby-card-why">' +
      '<span class="nearby-why-label">Why Recommended</span>' +
      '<p class="nearby-why-text">' + escapeHtml(item.why_recommended || '') + '</p>' +
      '</div>';

    return card;
  }

  // ── Category filters ──────────────────────────────────────────────
  if (categoryFilters) {
    categoryFilters.addEventListener('click', function (e) {
      var pill = e.target.closest('.nearby-filter-pill');
      if (!pill) return;

      document.querySelectorAll('.nearby-filter-pill').forEach(function (p) { p.classList.remove('active'); });
      pill.classList.add('active');
      currentFilter = pill.dataset.cat;
      if (allResults.length > 0) renderCards(allResults);
    });
  } else {
    console.warn('[SmartCampus] categoryFilters element not found!');
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
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function getCsrfToken() {
    var name = 'csrftoken=';
    var decoded = decodeURIComponent(document.cookie || '');
    var parts = decoded.split(';');
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return '';
  }

  // ── Event bindings ────────────────────────────────────────────────
  detectBtn.addEventListener('click', function () {
    locationResolved = false;
    requestLocation();
  });
  retryBtn.addEventListener('click', function () {
    if (userLat && userLon) fetchRecommendations();
    else { locationResolved = false; requestLocation(); }
  });

  // ── Init ──────────────────────────────────────────────────────────
  initShared();
  requestLocation();

})();
