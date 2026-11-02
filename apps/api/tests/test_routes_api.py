from fastapi.testclient import TestClient

from app.api.routes import get_routes_provider
from app.domain.schemas import PlaceDataStatus
from app.main import app
from tests.provider_fixtures import MockRoutesProvider

client = TestClient(app)


def test_route_estimate_endpoint_returns_mock_with_explicit_estimate_label() -> None:
    app.dependency_overrides[get_routes_provider] = MockRoutesProvider
    try:
        response = client.post(
            "/routes/estimate",
            json={
                "origin": {"latitude": 1.0, "longitude": 2.0},
                "destination": {"latitude": 1.1, "longitude": 2.1},
                "mode": "WALK",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["duration_minutes"] == 7
    assert body["distance_meters"] == 1200
    assert body["is_estimate"] is True
    assert body["data_status"] == PlaceDataStatus.MOCK.value
    assert "not a real travel-time estimate" in body["notice"]


def test_route_estimate_validates_coordinate_ranges() -> None:
    app.dependency_overrides[get_routes_provider] = MockRoutesProvider
    try:
        response = client.post(
            "/routes/estimate",
            json={
                "origin": {"latitude": 91, "longitude": 2},
                "destination": {"latitude": 1, "longitude": 2},
            },
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_route_endpoint_returns_503_when_google_key_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    response = client.post(
        "/routes/estimate",
        json={
            "origin": {"latitude": 1, "longitude": 2},
            "destination": {"latitude": 3, "longitude": 4},
        },
    )
    assert response.status_code == 503
