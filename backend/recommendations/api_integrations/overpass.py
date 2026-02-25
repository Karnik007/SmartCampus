"""
SmartCampus AI – OpenStreetMap Overpass API Integration
Fetches nearby points of interest (restaurants, cafes, parks, etc.) from OSM.
"""

import logging
import requests

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT = 25  # seconds


def _build_query(lat: float, lon: float, radius: int = 2000) -> str:
    """
    Build an Overpass QL query that fetches POIs within `radius` meters.
    Targets:  restaurant, cafe, marketplace, shops, leisure, tourism.
    """
    return f"""
    [out:json][timeout:{TIMEOUT}];
    (
      node["amenity"="restaurant"](around:{radius},{lat},{lon});
      node["amenity"="fast_food"](around:{radius},{lat},{lon});
      node["amenity"="cafe"](around:{radius},{lat},{lon});
      node["amenity"="bar"](around:{radius},{lat},{lon});
      node["amenity"="pub"](around:{radius},{lat},{lon});
      node["amenity"="marketplace"](around:{radius},{lat},{lon});
      node["shop"](around:{radius},{lat},{lon});
      node["leisure"="park"](around:{radius},{lat},{lon});
      node["leisure"="garden"](around:{radius},{lat},{lon});
      node["leisure"="sports_centre"](around:{radius},{lat},{lon});
      node["leisure"="stadium"](around:{radius},{lat},{lon});
      node["leisure"="playground"](around:{radius},{lat},{lon});
      node["leisure"="pitch"](around:{radius},{lat},{lon});
      node["tourism"](around:{radius},{lat},{lon});
      way["leisure"="park"](around:{radius},{lat},{lon});
      way["leisure"="garden"](around:{radius},{lat},{lon});
    );
    out center body;
    """


def _categorize(tags: dict) -> str:
    """Derive a human-readable category from OSM tags."""
    amenity = tags.get("amenity", "")
    if amenity in ("restaurant", "fast_food"):
        return "restaurant"
    if amenity in ("cafe", "bar", "pub"):
        return "cafe"
    if amenity == "marketplace":
        return "market"
    if "shop" in tags:
        shop = tags["shop"]
        if shop in ("supermarket", "convenience", "mall", "department_store"):
            return "market"
        return "shop"
    if "leisure" in tags:
        leisure = tags["leisure"]
        if leisure in ("park", "garden", "nature_reserve"):
            return "park"
        if leisure in ("sports_centre", "stadium", "pitch", "playground"):
            return "game_zone"
        return "leisure"
    if "tourism" in tags:
        return "tourism"
    return "other"


def fetch_nearby_places(lat: float, lon: float, radius: int = 2000) -> list[dict]:
    """
    Fetch nearby places from the Overpass API.

    Returns:
        List of dicts: {name, lat, lon, category, source}
    """
    query = _build_query(lat, lon, radius)

    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=TIMEOUT + 5,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.warning("Overpass API timed out for (%.4f, %.4f)", lat, lon)
        return []
    except requests.exceptions.RequestException as exc:
        logger.error("Overpass API error: %s", exc)
        return []
    except ValueError:
        logger.error("Overpass returned non-JSON response")
        return []

    results = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip unnamed POIs

        # Nodes have lat/lon directly; ways/relations use "center"
        e_lat = element.get("lat") or (element.get("center", {}) or {}).get("lat")
        e_lon = element.get("lon") or (element.get("center", {}) or {}).get("lon")
        if e_lat is None or e_lon is None:
            continue

        results.append({
            "name": name,
            "lat": e_lat,
            "lon": e_lon,
            "category": _categorize(tags),
            "rating": None,
            "open_now": None,
            "popular": False,
            "source": "OSM",
        })

    logger.info("Overpass returned %d named POIs near (%.4f, %.4f)", len(results), lat, lon)
    return results

