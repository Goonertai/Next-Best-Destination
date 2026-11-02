"""Place discovery and coordinate-validation use cases."""

from app.domain.geo import distance_between_meters
from app.domain.schemas import (
    GeoCoordinates,
    PlaceCategory,
    PlaceDataStatus,
    PlaceGroup,
    PlaceRecord,
    PlaceSearchResponse,
    PlaceValidationRequest,
    PlaceValidationResponse,
)
from app.providers.places import PlacesProvider

COORDINATE_MATCH_TOLERANCE_METERS = 100
PLACE_GROUP_RADIUS_METERS = 1_500


def group_places_geographically(
    places: list[PlaceRecord], *, radius_meters: int = PLACE_GROUP_RADIUS_METERS
) -> list[PlaceGroup]:
    """Group results around stable anchors using straight-line distance.

    The algorithm does not claim driving proximity or compute routes. Each place is
    assigned exactly once, within ``radius_meters`` of its group's first result.
    """
    remaining = list(places)
    groups: list[PlaceGroup] = []
    while remaining:
        anchor = remaining.pop(0)
        anchor_coordinates = GeoCoordinates(
            latitude=anchor.latitude,
            longitude=anchor.longitude,
        )
        members = [anchor]
        farther_places: list[PlaceRecord] = []
        max_distance = 0.0

        for place in remaining:
            coordinates = GeoCoordinates(latitude=place.latitude, longitude=place.longitude)
            distance = distance_between_meters(anchor_coordinates, coordinates)
            if distance <= radius_meters:
                members.append(place)
                max_distance = max(max_distance, distance)
            else:
                farther_places.append(place)

        groups.append(
            PlaceGroup(
                area_id=f"area-{len(groups) + 1}",
                anchor_place_id=anchor.place_id,
                radius_meters=round(max_distance),
                places=members,
            )
        )
        remaining = farther_places
    return groups


def search_places(
    provider: PlacesProvider,
    *,
    destination: str,
    category: PlaceCategory,
    limit: int,
) -> PlaceSearchResponse:
    query_term = "tourist attractions" if category == "attractions" else "restaurants"
    results = provider.search_text(f"{query_term} in {destination}", page_size=limit)
    groups = group_places_geographically(results)
    data_status = provider.data_status
    if data_status == PlaceDataStatus.MOCK:
        notice = "Mock fixture results only. No real place data is used."
    else:
        notice = "Results are sourced from Google Places API at retrieval time."
    return PlaceSearchResponse(
        destination=destination,
        category=category,
        results=results,
        groups=groups,
        data_status=data_status,
        notice=notice,
    )


def validate_place_reference(
    provider: PlacesProvider, request: PlaceValidationRequest
) -> PlaceValidationResponse:
    place = provider.get_place(request.place_id)
    if place is None:
        return PlaceValidationResponse(
            is_valid=False,
            data_status=provider.data_status,
            notice="The place ID was not found by the configured provider.",
        )

    supplied = request.coordinates
    canonical = GeoCoordinates(latitude=place.latitude, longitude=place.longitude)
    distance = distance_between_meters(supplied, canonical)
    is_valid = place.place_id == request.place_id and distance <= (
        COORDINATE_MATCH_TOLERANCE_METERS
    )
    return PlaceValidationResponse(
        is_valid=is_valid,
        place=place,
        distance_meters=round(distance, 1),
        match_tolerance_meters=COORDINATE_MATCH_TOLERANCE_METERS,
        data_status=provider.data_status,
        notice=(
            "Place ID and coordinates match current provider data within 100 meters."
            if is_valid
            else "Place ID was found, but the supplied coordinates differ by more than 100 meters."
        ),
    )
