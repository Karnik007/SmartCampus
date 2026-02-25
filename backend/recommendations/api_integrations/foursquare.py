"""
SmartCampus AI – Foursquare Places API Integration
Fetches nearby venues with ratings and categories.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

FOURSQUARE_URL = "https://api.foursquare.com/v3/places/search"
TIMEOUT = 15  # seconds


def _extract_category(categories: list) -> str:
    """Pull the primary category name from Foursquare's category list."""
    if not categories:
        return "place"
    name = categories[0].get("name", "place").lower()
    # Map to our standard categories
    mapping = {
        "restaurant": "restaurant",
        "dining": "restaurant",
        "food": "restaurant",
        "cafe": "cafe",
        "coffee": "cafe",
        "tea": "cafe",
        "bar": "cafe",
        "market": "market",
        "supermarket": "market",
        "grocery": "market",
        "shop": "shop",
        "store": "shop",
        "park": "park",
        "garden": "park",
        "playground": "game_zone",
        "arcade": "game_zone",
        "game": "game_zone",
        "sport": "game_zone",
        "gym": "game_zone",
        "entertainment": "game_zone",
    }
    for keyword, category in mapping.items():
        if keyword in name:
            return category
    return "place"


def fetch_nearby_places(lat: float, lon: float, radius: int = 2000) -> list[dict]:
    """
    Fetch nearby places from the Foursquare Places API.

    Returns:
        List of dicts: {name, lat, lon, rating, category, source}
    """
    api_key = getattr(settings, "FOURSQUARE_API_KEY", "")
    if not api_key:
        logger.warning("FOURSQUARE_API_KEY not configured — skipping Foursquare")
        return []

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
    }
    params = {
        "ll": f"{lat},{lon}",
        "radius": radius,
        "limit": 10,
    }

    try:
        resp = requests.get(
            FOURSQUARE_URL,
            headers=headers,
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.warning("Foursquare API timed out for (%.4f, %.4f)", lat, lon)
        return []
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else "?"
        if status_code == 429:
            logger.warning("Foursquare API rate limit hit")
        else:
            logger.error("Foursquare HTTP error %s: %s", status_code, exc)
        return []
    except requests.exceptions.RequestException as exc:
        logger.error("Foursquare API error: %s", exc)
        return []
    except ValueError:
        logger.error("Foursquare returned non-JSON response")
        return []

    results = []
    for venue in data.get("results", []):
        name = venue.get("name")
        if not name:
            continue

        geocodes = venue.get("geocodes", {}).get("main", {})
        v_lat = geocodes.get("latitude")
        v_lon = geocodes.get("longitude")
        if v_lat is None or v_lon is None:
            continue

        rating = venue.get("rating")
        if rating and rating > 5:
            rating = round(rating / 2, 1)  # normalise 10-scale to 5-scale

        results.append({
            "name": name,
            "lat": v_lat,
            "lon": v_lon,
            "category": _extract_category(venue.get("categories", [])),
            "rating": rating,
            "open_now": None,
            "popular": venue.get("popularity", 0) > 0.7 if venue.get("popularity") else False,
            "source": "Foursquare",
        })

    logger.info("Foursquare returned %d places near (%.4f, %.4f)", len(results), lat, lon)
    return results
