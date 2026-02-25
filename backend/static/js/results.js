/* ===================================================
   SmartCampus AI – Results Page (v4 – Live Location)
   Geolocation → /get-recommendations/ → render cards
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

  // ── Helpers ───────────────────────────────────────────────────────
  const show = el => { if (el) el.style.display = ''; };
  const hide = el => { if (el) el.style.display = 'none'; };

  const CATEGORY_ICONS = {
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
  };

  // ── Category matching ─────────────────────────────────────────────
  // Maps each filter pill value to all API category strings it should match.
  const CATEGORY_MAP = {
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

    // Check exact match first, then substring containment both ways
    for (const m of validMatches) {
      if (cat === m || cat.includes(m) || m.includes(cat)) return true;
    }
    return false;
  }

  // ── Geolocation ───────────────────────────────────────────────────
  function requestLocation() {
    if (!navigator.geolocation) {
      showError('Geolocation is not supported by your browser.');
      return;
    }

    locationLabel.textContent = 'Detecting location…';
    detectBtn.disabled = true;
    detectBtn.innerHTML = '<div class="nearby-btn-spinner"></div><span>Detecting…</span>';

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
    locationCoords.textContent = userLat.toFixed(4) + ', ' + userLon.toFixed(4);
    detectBtn.disabled = false;
    detectBtn.innerHTML =
      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><circle cx="12" cy="12" r="3"/></svg>' +
      '<span>Refresh Location</span>';

    fetchRecommendations();
  }

  function onLocationError(err) {
    detectBtn.disabled = false;
    detectBtn.innerHTML =
      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><circle cx="12" cy="12" r="3"/></svg>' +
      '<span>Detect My Location</span>';

    var msgs = {
      1: 'Location access denied. Please allow location permission and try again.',
      2: 'Unable to determine your location. Check your network.',
      3: 'Location request timed out. Please try again.',
    };
    showError(msgs[err.code] || 'Could not get your location.');
  }

  // ── Fetch recommendations ─────────────────────────────────────────
  function fetchRecommendations() {
    hide(nearbyError);
    hide(nearbyEmpty);
    hide(categoryFilters);
    hide(resultsInfo);
    nearbyGrid.innerHTML = '';
    show(nearbyLoading);

    fetch('/get-recommendations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: userLat,
        longitude: userLon,
        preferences: ['restaurant', 'cafe', 'park', 'event', 'market', 'game_zone'],
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
        hide(nearbyLoading);

        console.log('[SmartCampus] API returned', data.length, 'items');
        console.log('[SmartCampus] Categories:', data.map(function (d) { return d.category }).join(', '));

        if (!Array.isArray(data) || data.length === 0) {
          show(nearbyEmpty);
          return;
        }

        allResults = data;
        currentFilter = 'all';

        // Reset filter pills
        var pills = document.querySelectorAll('.nearby-filter-pill');
        pills.forEach(function (p) { p.classList.remove('active'); });
        var allPill = document.querySelector('.nearby-filter-pill[data-cat="all"]');
        if (allPill) allPill.classList.add('active');

        show(categoryFilters);
        renderCards(allResults);
      })
      .catch(function (e) {
        hide(nearbyLoading);
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

    console.log('[SmartCampus] Filter:', currentFilter, '→ matched', filtered.length, 'of', items.length);

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

      console.log('[SmartCampus] Filter clicked:', pill.dataset.cat);

      document.querySelectorAll('.nearby-filter-pill').forEach(function (p) { p.classList.remove('active'); });
      pill.classList.add('active');
      currentFilter = pill.dataset.cat;

      console.log('[SmartCampus] allResults length:', allResults.length);
      if (allResults.length > 0) {
        console.log('[SmartCampus] First item category:', allResults[0].category);
      }

      renderCards(allResults);
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

  // ── Event bindings ────────────────────────────────────────────────
  detectBtn.addEventListener('click', requestLocation);
  retryBtn.addEventListener('click', function () {
    if (userLat && userLon) fetchRecommendations();
    else requestLocation();
  });

  // ── Init ──────────────────────────────────────────────────────────
  initShared();
  requestLocation();

})();
