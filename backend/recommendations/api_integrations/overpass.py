"""
SmartCampus AI – OpenStreetMap Overpass API Integration
Fetches nearby points of interest (restaurants, cafes, parks, etc.) from OSM.
Uses multiple mirror URLs for resilience against public-instance overloads.
"""

import logging
import requests

logger = logging.getLogger(__name__)

# Multiple Overpass mirrors for resilience (tried in order)
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
QUERY_TIMEOUT = 15   # Overpass QL [timeout:…] value (seconds)
REQUEST_TIMEOUT = 20  # Python requests timeout (seconds)


def _build_query(lat: float, lon: float, radius: int = 2000) -> str:
    """
    Build an Overpass QL query that fetches POIs within `radius` meters.
    Targets:  restaurant, cafe, marketplace, shops, leisure, tourism.
    """
    return f"""
    [out:json][timeout:{QUERY_TIMEOUT}];
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
    Tries multiple mirrors in order for resilience.

    Returns:
        List of dicts: {name, lat, lon, category, source}
    """
    query = _build_query(lat, lon, radius)
    data = None
    last_error = None

    for mirror_url in OVERPASS_MIRRORS:
        try:
            resp = requests.post(
                mirror_url,
                data={"data": query},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("Overpass mirror %s succeeded", mirror_url.split("//")[1].split("/")[0])
            break  # success — stop trying mirrors
        except requests.exceptions.Timeout:
            logger.warning("Overpass mirror %s timed out", mirror_url)
            last_error = f"timeout at {mirror_url}"
        except requests.exceptions.RequestException as exc:
            logger.warning("Overpass mirror %s failed: %s", mirror_url, exc)
            last_error = str(exc)
        except ValueError:
            logger.warning("Overpass mirror %s returned non-JSON", mirror_url)
            last_error = f"non-JSON from {mirror_url}"

    if data is None:
        logger.warning(
            "All Overpass mirrors failed for (%.4f, %.4f). Last error: %s",
            lat, lon, last_error,
        )
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
