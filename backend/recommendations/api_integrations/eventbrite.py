"""
SmartCampus AI – Eventbrite API Integration
Fetches nearby events within a given radius.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EVENTBRITE_URL = "https://www.eventbriteapi.com/v3/events/search/"
TIMEOUT = 15  # seconds


def fetch_nearby_events(lat: float, lon: float, radius: str = "5km") -> list[dict]:
    """
    Fetch nearby events from the Eventbrite API.

    Returns:
        List of dicts: {name, lat, lon, category, source}
    """
    token = getattr(settings, "EVENTBRITE_TOKEN", "")
    if not token:
        logger.warning("EVENTBRITE_TOKEN not configured — skipping Eventbrite")
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {
        "location.latitude": str(lat),
        "location.longitude": str(lon),
        "location.within": radius,
    }

    try:
        resp = requests.get(
            EVENTBRITE_URL,
            headers=headers,
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.warning("Eventbrite API timed out for (%.4f, %.4f)", lat, lon)
        return []
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        error_text = str(exc)
        if status_code == 429:
            logger.warning("Eventbrite API rate limit hit")
        elif status_code in (401, 403, 404) or any(code in error_text for code in ("401", "403", "404")):
            logger.warning("Eventbrite API not usable (status %s). Check token/config; skipping source.", status_code)
        else:
            logger.error("Eventbrite HTTP error %s: %s", status_code, exc)
        return []
    except requests.exceptions.RequestException as exc:
        logger.error("Eventbrite API error: %s", exc)
        return []
    except ValueError:
        logger.error("Eventbrite returned non-JSON response")
        return []

    results = []
    for event in data.get("events", []):
        name_obj = event.get("name", {})
        name = name_obj.get("text") if isinstance(name_obj, dict) else str(name_obj)
        if not name:
            continue

        # Eventbrite venue coordinates
        venue = event.get("venue", {}) or {}
        v_lat = venue.get("latitude") or venue.get("address", {}).get("latitude")
        v_lon = venue.get("longitude") or venue.get("address", {}).get("longitude")

        # Fall back to the search location if venue coords missing
        try:
            v_lat = float(v_lat) if v_lat else lat
            v_lon = float(v_lon) if v_lon else lon
        except (TypeError, ValueError):
            v_lat, v_lon = lat, lon

        results.append({
            "name": name,
            "lat": v_lat,
            "lon": v_lon,
            "category": "event",
            "rating": None,
            "open_now": True,  # events are inherently "happening"
            "popular": event.get("is_free", False) or event.get("capacity", 0) > 100,
            "source": "Eventbrite",
        })

    logger.info("Eventbrite returned %d events near (%.4f, %.4f)", len(results), lat, lon)
    return results
