"""End-to-end API coverage across draft, place, route, and weather workflows."""

from fastapi.testclient import TestClient

from app.api.places import get_places_provider
from app.api.routes import get_routes_provider
from app.api.weather import get_weather_data_provider
from app.main import app
from tests.provider_fixtures import (
    MockPlacesProvider,
    MockRoutesProvider,
    MockWeatherProvider,
)

client = TestClient(app)


def test_trip_generation_to_sourced_data_endpoints_stays_explicit_about_fixtures() -> None:
    app.dependency_overrides[get_places_provider] = MockPlacesProvider
    app.dependency_overrides[get_routes_provider] = MockRoutesProvider
    app.dependency_overrides[get_weather_data_provider] = MockWeatherProvider
    try:
        generated = client.post(
            "/itineraries/generate",
            json={
                "destination": "Fixture City",
                "start_date": "2026-11-10",
                "end_date": "2026-11-12",
                "total_budget": "1000",
                "currency": "CAD",
                "travelers": 2,
                "interests": ["History"],
                "pace": "balanced",
            },
        )
        attractions = client.get("/places/attractions", params={"destination": "Fixture City"})
        validation = client.post(
            "/places/validate",
            json={
                "place_id": "mock-place-1",
                "coordinates": {"latitude": 1.0, "longitude": 2.0},
            },
        )
        route = client.post(
            "/routes/estimate",
            json={
                "origin": {"latitude": 1.0, "longitude": 2.0},
                "destination": {"latitude": 1.1, "longitude": 2.1},
                "mode": "WALK",
            },
        )
        weather = client.post(
            "/weather/forecast",
            json={
                "coordinates": {"latitude": 1.0, "longitude": 2.0},
                "forecast_date": "2026-11-10",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert all(
        response.status_code == 200
        for response in (generated, attractions, validation, route, weather)
    )
    assert generated.json()["uses_verified_place_data"] is False
    assert attractions.json()["data_status"] == "mock"
    assert attractions.json()["results"][0]["source"]["provider"].startswith("Mock fixture")
    assert attractions.json()["groups"][0]["places"][0]["data_status"] == "mock"
    assert validation.json()["is_valid"] is True
    assert validation.json()["data_status"] == "mock"
    assert route.json()["is_estimate"] is True
    assert route.json()["data_status"] == "mock"
    assert weather.json()["data_status"] == "mock"
    assert weather.json()["forecast"]["source"]["provider"].startswith("Mock fixture")
