"""
SmartCampus AI – Location-Based Recommendation Service
Aggregates data from Overpass, Foursquare, and Eventbrite,
scores places with an AI algorithm, and returns top recommendations.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.cache import cache

from recommendations.api_integrations import overpass, foursquare, eventbrite
from recommendations.utils.distance import haversine, haversine_km

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 minutes
MAX_RESULTS = 15

# Default user preference tags — used when none provided
DEFAULT_PREFERENCES = ["restaurant", "cafe", "park", "event"]


def _compute_score(place: dict, user_lat: float, user_lon: float, preferences: list) -> float:
    """
    AI scoring algorithm.

    score =
        +3  if category matches a user preference tag
        +2  if rating > 4
        -(distance_in_meters / 500)
        +1  if open_now
        +2  if popular
    """
    score = 0.0

    # Category match
    category = place.get("category", "").lower()
    if any(pref.lower() in category or category in pref.lower() for pref in preferences):
        score += 3

    # Rating bonus
    rating = place.get("rating")
    if rating is not None:
        try:
            if float(rating) > 4:
                score += 2
        except (TypeError, ValueError):
            pass  # treat as neutral

    # Distance penalty
    p_lat = place.get("lat")
    p_lon = place.get("lon")
    if p_lat is not None and p_lon is not None:
        dist_m = haversine(user_lat, user_lon, p_lat, p_lon)
        score -= dist_m / 500
    else:
        dist_m = 0

    # Open now bonus
    if place.get("open_now"):
        score += 1

    # Popularity bonus
    if place.get("popular"):
        score += 2

    return round(score, 2)


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

    return {
        "name": place.get("name", "Unknown"),
        "category": place.get("category", "place"),
        "distance_km": dist_km,
        "rating": place.get("rating"),
        "source": place.get("source", ""),
        "score": score,
        "why_recommended": why,
    }


def get_nearby_recommendations(
    lat: float,
    lon: float,
    preferences: list | None = None,
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
    cache_key = f"recommend_{lat_r}_{lon_r}"

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Cache HIT for %s", cache_key)
        return cached

    prefs = preferences or DEFAULT_PREFERENCES

    # ── Fetch from all three sources concurrently ─────────────────────
    all_places: list[dict] = []
    fetch_tasks = {
        "overpass": lambda: overpass.fetch_nearby_places(lat, lon),
        "foursquare": lambda: foursquare.fetch_nearby_places(lat, lon),
        "eventbrite": lambda: eventbrite.fetch_nearby_events(lat, lon),
    }

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn): name for name, fn in fetch_tasks.items()}
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                places = future.result()
                all_places.extend(places)
                logger.info("%s returned %d items", source_name, len(places))
            except Exception as exc:
                logger.error("%s fetch failed: %s", source_name, exc)

    # ── Enrich, score, sort ───────────────────────────────────────────
    enriched = [_enrich_place(p, lat, lon, prefs) for p in all_places]
    enriched.sort(key=lambda x: x["score"], reverse=True)
    top = enriched[:MAX_RESULTS]

    # ── Cache ─────────────────────────────────────────────────────────
    cache.set(cache_key, top, CACHE_TTL)
    logger.info("Cached %d results under %s", len(top), cache_key)

    return top
