from fastapi.testclient import TestClient

from app.api.places import get_places_provider
from app.domain.schemas import PlaceDataStatus
from app.main import app
from tests.provider_fixtures import MockPlacesProvider

client = TestClient(app)


def test_attraction_discovery_marks_fixture_results_as_mock() -> None:
    provider = MockPlacesProvider()
    app.dependency_overrides[get_places_provider] = lambda: provider
    try:
        response = client.get("/places/attractions", params={"destination": "Fixture City"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "attractions"
    assert body["data_status"] == PlaceDataStatus.MOCK.value
    assert "No real place data" in body["notice"]
    assert body["results"][0]["place_id"] == "mock-place-1"
    assert provider.queries == [("tourist attractions in Fixture City", 10)]


def test_restaurant_discovery_uses_category_query_and_limit() -> None:
    provider = MockPlacesProvider()
    app.dependency_overrides[get_places_provider] = lambda: provider
    try:
        response = client.get(
            "/places/restaurants",
            params={"destination": "Fixture City", "limit": 3},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["category"] == "restaurants"
    assert provider.queries == [("restaurants in Fixture City", 3)]


def test_place_validation_checks_provider_id_and_coordinate_distance() -> None:
    app.dependency_overrides[get_places_provider] = MockPlacesProvider
    try:
        valid_response = client.post(
            "/places/validate",
            json={
                "place_id": "mock-place-1",
                "coordinates": {"latitude": 1.0001, "longitude": 2.0001},
            },
        )
        mismatch_response = client.post(
            "/places/validate",
            json={
                "place_id": "mock-place-1",
                "coordinates": {"latitude": 1.01, "longitude": 2.01},
            },
        )
        missing_response = client.post(
            "/places/validate",
            json={
                "place_id": "unknown-fixture",
                "coordinates": {"latitude": 1.0, "longitude": 2.0},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert valid_response.json()["is_valid"] is True
    assert valid_response.json()["distance_meters"] < 100
    assert mismatch_response.json()["is_valid"] is False
    assert mismatch_response.json()["distance_meters"] > 100
    assert missing_response.json()["place"] is None
    assert missing_response.json()["is_valid"] is False


def test_place_endpoints_return_503_when_google_key_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    response = client.get("/places/attractions", params={"destination": "Fixture City"})
    assert response.status_code == 503
