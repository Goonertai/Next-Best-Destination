from app.domain.schemas import PlaceRecord
from app.services.places import PLACE_GROUP_RADIUS_METERS, group_places_geographically
from tests.provider_fixtures import mock_place


def place_at(place_id: str, *, latitude: float, longitude: float) -> PlaceRecord:
    return mock_place(place_id).model_copy(update={"latitude": latitude, "longitude": longitude})


def test_groups_nearby_places_and_keeps_distant_places_in_separate_areas() -> None:
    places = [
        place_at("near-anchor", latitude=0, longitude=0),
        place_at("nearby", latitude=0, longitude=0.005),
        place_at("distant", latitude=0, longitude=0.03),
    ]

    groups = group_places_geographically(places)

    assert [group.area_id for group in groups] == ["area-1", "area-2"]
    assert [place.place_id for place in groups[0].places] == ["near-anchor", "nearby"]
    assert groups[0].anchor_place_id == "near-anchor"
    assert groups[0].radius_meters < PLACE_GROUP_RADIUS_METERS
    assert [place.place_id for place in groups[1].places] == ["distant"]
    assert groups[1].radius_meters == 0


def test_group_radius_is_measured_from_anchor_not_chained_between_neighbors() -> None:
    # Each adjacent pair is under 1.5 km, but the last place is over 1.5 km
    # from the first result and should start a new group.
    places = [
        place_at("first", latitude=0, longitude=0),
        place_at("second", latitude=0, longitude=0.01),
        place_at("third", latitude=0, longitude=0.02),
    ]

    groups = group_places_geographically(places)

    assert [[place.place_id for place in group.places] for group in groups] == [
        ["first", "second"],
        ["third"],
    ]


def test_empty_search_results_produce_no_groups() -> None:
    assert group_places_geographically([]) == []
