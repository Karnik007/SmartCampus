"""
SmartCampus AI – Haversine Distance Calculator
Accurate great-circle distance between two GPS coordinates.
"""

import math


# Earth's mean radius in meters
_EARTH_RADIUS_M = 6_371_000


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (decimal degrees).
        lat2, lon2: Latitude and longitude of point 2 (decimal degrees).

    Returns:
        Distance in **meters**.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_M * c


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the haversine distance in **kilometers**, rounded to 2 decimals."""
    return round(haversine(lat1, lon1, lat2, lon2) / 1000, 2)
