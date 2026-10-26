"""Small geographic helpers used to validate provider coordinates."""

from math import asin, cos, radians, sin, sqrt

from app.domain.schemas import GeoCoordinates

EARTH_RADIUS_METERS = 6_371_000


def distance_between_meters(first: GeoCoordinates, second: GeoCoordinates) -> float:
    """Calculate great-circle distance between two validated points."""
    latitude_delta = radians(second.latitude - first.latitude)
    longitude_delta = radians(second.longitude - first.longitude)
    first_latitude = radians(first.latitude)
    second_latitude = radians(second.latitude)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(first_latitude) * cos(second_latitude) * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(min(1.0, haversine)))
