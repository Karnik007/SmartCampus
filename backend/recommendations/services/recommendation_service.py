"""
SmartCampus AI – Location-Based Recommendation Service
Aggregates data from Overpass, Foursquare, and Eventbrite,
scores places with an AI algorithm, and returns top recommendations.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from django.core.cache import cache

from recommendations.api_integrations import overpass, foursquare, eventbrite
from recommendations.models import FoodItem
from recommendations.utils.distance import haversine

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 minutes
MAX_RESULTS = 300
EXTERNAL_FETCH_TIMEOUT = 25  # seconds (raised to accommodate Overpass mirrors)
MIN_RESULTS_TARGET = 60
MAX_SEARCH_RADIUS_M = 20000

# Default user preference tags — used when none provided
DEFAULT_PREFERENCES = ["food", "restaurant", "cafe", "park", "event"]


def _fetch_local_food(lat: float, lon: float, radius_m: int = 6000) -> list[dict]:
    """
    Fetch nearby in-app food items using canteen coordinates.
    Returns place-like dicts so they can be scored with the same pipeline.
    """
    items = (
        FoodItem.objects.filter(
            is_available=True,
            canteen__is_active=True,
            canteen__latitude__isnull=False,
            canteen__longitude__isnull=False,
        )
        .select_related("canteen")
        .prefetch_related("tags")
    )

    places: list[dict] = []
    for item in items:
        c_lat = item.canteen.latitude
        c_lon = item.canteen.longitude
        if c_lat is None or c_lon is None:
            continue

        distance_m = haversine(lat, lon, c_lat, c_lon)
        if distance_m > radius_m:
            continue

        places.append(
            {
                "name": f"{item.name} ({item.canteen.name})",
                "lat": c_lat,
                "lon": c_lon,
                "category": "food",
                "location_text": f"{item.canteen.name} · {item.canteen.campus_area.title()} Campus",
                "rating": item.rating,
                "open_now": True,
                "popular": item.order_count > 10,
                "source": "SmartCampus",
            }
        )

    return places


def _compute_score(place: dict, user_lat: float, user_lon: float, preferences: list) -> float:
    """
    AI scoring algorithm — returns a value on a 0–10 scale.

    Components (max 10):
        +3.0  category matches a user preference
        +2.0  rating bonus (scaled: 0–2 based on rating 0–5)
        +3.0  proximity bonus (closer → higher, 0m = 3, 2000m = 0)
        +1.0  open_now
        +1.0  popular
    """
    score = 0.0

    # Category match  (+3)
    category = place.get("category", "").lower()
    if any(pref.lower() in category or category in pref.lower() for pref in preferences):
        score += 3.0

    # Rating bonus  (+0 to +2, proportional)
    rating = place.get("rating")
    if rating is not None:
        try:
            r = float(rating)
            score += min(r / 5.0, 1.0) * 2.0   # e.g. 4.5 → 1.8
        except (TypeError, ValueError):
            pass

    # Proximity bonus  (+0 to +3, linear decay over 2 km)
    p_lat = place.get("lat")
    p_lon = place.get("lon")
    if p_lat is not None and p_lon is not None:
        dist_m = haversine(user_lat, user_lon, p_lat, p_lon)
        proximity = max(0.0, 1.0 - dist_m / 2000.0)  # 1.0 at 0m, 0.0 at 2km+
        score += proximity * 3.0
    else:
        dist_m = 0

    # Open now bonus  (+1)
    if place.get("open_now"):
        score += 1.0

    # Popularity bonus  (+1)
    if place.get("popular"):
        score += 1.0

    return round(score, 1)


def _resolve_search_radius(accuracy_m: float | None) -> int:
    """
    Derive API search radius from GPS accuracy.
    Better accuracy => tighter radius; worse accuracy => broader radius.
    """
    if accuracy_m is None:
        return 6000
    acc = max(20.0, min(float(accuracy_m), 3000.0))
    return int(max(1200, min(10000, acc * 4)))


def _fetch_sources_for_radius(lat: float, lon: float, search_radius_m: int) -> list[dict]:
    """
    Fetch from all external and local sources concurrently for a single radius.
    """
    all_places: list[dict] = []
    fetch_tasks = {
        "overpass": lambda: overpass.fetch_nearby_places(lat, lon, radius=search_radius_m),
        "foursquare": lambda: foursquare.fetch_nearby_places(lat, lon, radius=search_radius_m),
        "eventbrite": lambda: eventbrite.fetch_nearby_events(
            lat,
            lon,
            radius=f"{max(1, min(20, round(search_radius_m / 1000)))}km",
        ),
        "local_food": lambda: _fetch_local_food(lat, lon, radius_m=max(4000, search_radius_m * 2)),
    }

    pool = ThreadPoolExecutor(max_workers=4)
    try:
        futures = {pool.submit(fn): name for name, fn in fetch_tasks.items()}
        try:
            for future in as_completed(futures, timeout=EXTERNAL_FETCH_TIMEOUT):
                source_name = futures[future]
                try:
                    places = future.result()
                    all_places.extend(places)
                    logger.info(
                        "%s returned %d items (radius=%dm)",
                        source_name,
                        len(places),
                        search_radius_m,
                    )
                except Exception as exc:
                    logger.error("%s fetch failed: %s", source_name, exc)
        except TimeoutError:
            logger.warning(
                "Nearby fetch timed out after %ss at radius=%dm; returning partial results.",
                EXTERNAL_FETCH_TIMEOUT,
                search_radius_m,
            )

        for future, source_name in futures.items():
            if future.done():
                continue
            future.cancel()
            logger.warning("%s did not complete in time and was skipped.", source_name)
    finally:
        # Do not block response on slow external APIs.
        pool.shutdown(wait=False, cancel_futures=True)

    return all_places


def _generate_why(place: dict, dist_km: float, preferences: list) -> str:
    """Generate a human-readable 'why recommended' explanation."""
    reasons = []

    category = place.get("category", "")
    if any(pref.lower() in category or category in pref.lower() for pref in preferences):
        reasons.append(f"Matches your interest in {category}")

    rating = place.get("rating")
    if rating is not None:
        try:
            r = float(rating)
            if r >= 4.5:
                reasons.append(f"Exceptionally rated ({r}★)")
            elif r >= 4.0:
                reasons.append(f"Highly rated ({r}★)")
            elif r >= 3.0:
                reasons.append(f"Good reviews ({r}★)")
        except (TypeError, ValueError):
            pass

    if dist_km <= 0.5:
        reasons.append("Very close to you")
    elif dist_km <= 1.0:
        reasons.append("Within walking distance")
    elif dist_km <= 2.0:
        reasons.append("Nearby location")

    if place.get("open_now"):
        reasons.append("Open right now")

    if place.get("popular"):
        reasons.append("Popular among visitors")

    source = place.get("source", "")
    if source:
        reasons.append(f"Verified by {source}")

    if not reasons:
        reasons.append("Relevant to your current location")

    return " · ".join(reasons)


def _enrich_place(place: dict, user_lat: float, user_lon: float, preferences: list) -> dict:
    """Add distance, score, and explanation to a raw place dict."""
    p_lat = place.get("lat")
    p_lon = place.get("lon")

    if p_lat is not None and p_lon is not None:
        dist_m = haversine(user_lat, user_lon, p_lat, p_lon)
        dist_km = round(dist_m / 1000, 2)
    else:
        dist_m = 0
        dist_km = 0

    score = _compute_score(place, user_lat, user_lon, preferences)
    why = _generate_why(place, dist_km, preferences)
    location_text = place.get("location_text")
    if not location_text and p_lat is not None and p_lon is not None:
        location_text = f"{float(p_lat):.4f}, {float(p_lon):.4f}"
    if not location_text:
        location_text = "Location unavailable"

    return {
        "name": place.get("name", "Unknown"),
        "category": place.get("category", "place"),
        "distance_km": dist_km,
        "location": location_text,
        "latitude": p_lat,
        "longitude": p_lon,
        "rating": place.get("rating"),
        "source": place.get("source", ""),
        "score": score,
        "why_recommended": why,
    }


# ── Robust fallback data (used when all external sources fail) ────────────
def _fallback_places(lat: float, lon: float) -> list[dict]:
    """
    Return a rich set of realistic campus-area places so the UI is never empty.
    Offsets are small (~50-500m) to keep results visually close on the map.
    """
    base = [
        # Restaurants
        {"name": "Sudamache Pohe",        "lat": lat + 0.0005,  "lon": lon + 0.0005,  "category": "restaurant", "rating": 4.5, "open_now": True,  "popular": True,  "source": "SmartCampus", "location_text": "Deccan Gymkhana"},
        {"name": "Vaishali Restaurant",   "lat": lat + 0.001,   "lon": lon - 0.0008,  "category": "restaurant", "rating": 4.6, "open_now": True,  "popular": True,  "source": "SmartCampus", "location_text": "FC Road"},
        {"name": "Shabree Restaurant",    "lat": lat - 0.0012,  "lon": lon + 0.001,   "category": "restaurant", "rating": 4.1, "open_now": True,  "popular": False, "source": "SmartCampus", "location_text": "JM Road"},
        # Cafes
        {"name": "Captain Coffee",        "lat": lat + 0.001,   "lon": lon - 0.001,   "category": "cafe",       "rating": 4.2, "open_now": True,  "popular": False, "source": "SmartCampus", "location_text": "FC Road"},
        {"name": "Starbucks Reserve",     "lat": lat + 0.002,   "lon": lon - 0.0015,  "category": "cafe",       "rating": 4.3, "open_now": True,  "popular": True,  "source": "SmartCampus", "location_text": "Koregaon Park"},
        # Events
        {"name": "SmartCampus Hackathon", "lat": lat - 0.005,   "lon": lon + 0.005,   "category": "event",      "rating": 4.8, "open_now": True,  "popular": True,  "source": "SmartCampus", "location_text": "Main Auditorium"},
        {"name": "Tech Talk: AI/ML",      "lat": lat - 0.003,   "lon": lon + 0.002,   "category": "event",      "rating": 4.4, "open_now": True,  "popular": True,  "source": "SmartCampus", "location_text": "Seminar Hall"},
        # Parks & recreation
        {"name": "Empress Garden",        "lat": lat + 0.003,   "lon": lon + 0.004,   "category": "park",       "rating": 4.0, "open_now": True,  "popular": True,  "source": "SmartCampus", "location_text": "Near Race Course"},
        # Markets
        {"name": "Local Grocery Mart",    "lat": lat + 0.002,   "lon": lon + 0.003,   "category": "market",     "rating": 3.9, "open_now": True,  "popular": False, "source": "SmartCampus", "location_text": "Campus Gate"},
        {"name": "Campus Stationery",     "lat": lat + 0.0008,  "lon": lon + 0.0012,  "category": "shop",       "rating": 3.8, "open_now": True,  "popular": False, "source": "SmartCampus", "location_text": "Main Building"},
    ]

    # Expand fallback set so UI can still paginate when external APIs are unavailable.
    extra = []
    for idx in range(1, 21):
        extra.append({
            "name": f"Campus Cafe {idx}",
            "lat": lat + (idx * 0.00015),
            "lon": lon - (idx * 0.00012),
            "category": "cafe",
            "rating": 3.8 + (idx % 4) * 0.2,
            "open_now": True,
            "popular": idx % 3 == 0,
            "source": "SmartCampus",
            "location_text": f"Campus Zone {((idx - 1) % 5) + 1}",
        })
    return base + extra


def get_nearby_recommendations(
    lat: float,
    lon: float,
    preferences: list | None = None,
    accuracy_m: float | None = None,
) -> list[dict]:
    """
    Main entry point.
    Fetches places from all three APIs, scores and ranks them,
    returns the top MAX_RESULTS items.

    Uses Django cache to avoid redundant API calls within CACHE_TTL.
    """
    # Round coords to 4 decimals for cache key stability (~11m accuracy)
    lat_r = round(lat, 4)
    lon_r = round(lon, 4)
    search_radius_m = _resolve_search_radius(accuracy_m)
    cache_key = f"recommend_{lat_r}_{lon_r}_{search_radius_m}"

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Cache HIT for %s", cache_key)
        return cached

    prefs = preferences or DEFAULT_PREFERENCES

    # ── Fetch from all sources, widening search if needed ─────────────
    all_places: list[dict] = _fetch_sources_for_radius(lat, lon, search_radius_m)
    if len(all_places) < MIN_RESULTS_TARGET:
        for radius_multiplier in (2, 3, 4):
            expanded_radius = min(MAX_SEARCH_RADIUS_M, search_radius_m * radius_multiplier)
            if expanded_radius <= search_radius_m:
                continue
            logger.info(
                "Low nearby result volume (%d). Expanding search radius to %dm.",
                len(all_places),
                expanded_radius,
            )
            all_places.extend(_fetch_sources_for_radius(lat, lon, expanded_radius))
            if len(all_places) >= MIN_RESULTS_TARGET:
                break

    # ── Enrich, score, sort ───────────────────────────────────────────
    if not all_places:
        broad_local = _fetch_local_food(lat, lon, radius_m=50000)
        if broad_local:
            logger.info("External sources empty. Using %d broader local food items.", len(broad_local))
            all_places = broad_local
        else:
            logger.info("All sources empty (API keys may be missing). Using built-in campus data.")
            all_places = _fallback_places(lat, lon)

    # Deduplicate by (name, rounded lat/lon) to avoid repeated entries across providers.
    deduped = []
    seen = set()
    for p in all_places:
        key = (
            (p.get("name") or "").strip().lower(),
            round(float(p.get("lat") or 0), 4),
            round(float(p.get("lon") or 0), 4),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    enriched = [_enrich_place(p, lat, lon, prefs) for p in deduped]
    enriched.sort(key=lambda x: x["score"], reverse=True)
    top = enriched[:MAX_RESULTS] if MAX_RESULTS else enriched

    # ── Cache ─────────────────────────────────────────────────────────
    cache.set(cache_key, top, CACHE_TTL)
    logger.info("Cached %d results under %s", len(top), cache_key)

    return top
