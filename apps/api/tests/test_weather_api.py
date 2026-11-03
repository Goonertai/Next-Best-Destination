from fastapi.testclient import TestClient

from app.api.weather import get_weather_data_provider
from app.domain.schemas import PlaceDataStatus
from app.main import app
from tests.provider_fixtures import MockWeatherProvider, UnavailableWeatherProvider

client = TestClient(app)

REQUEST = {
    "coordinates": {"latitude": 43.6532, "longitude": -79.3832},
    "forecast_date": "2026-11-10",
}


def test_weather_endpoint_returns_mock_forecast_with_clear_notice() -> None:
    app.dependency_overrides[get_weather_data_provider] = MockWeatherProvider
    try:
        response = client.post("/weather/forecast", json=REQUEST)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] == PlaceDataStatus.MOCK.value
    assert body["forecast"]["forecast_date"] == "2026-11-10"
    assert body["forecast"]["temperature_max_c"] == 14.0
    assert body["forecast"]["source"]["provider"].startswith("Mock fixture")
    assert "not current or real weather data" in body["notice"]


def test_weather_failure_returns_unavailable_without_a_forecast() -> None:
    app.dependency_overrides[get_weather_data_provider] = UnavailableWeatherProvider
    try:
        response = client.post("/weather/forecast", json=REQUEST)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["forecast"] is None
    assert body["data_status"] == PlaceDataStatus.UNAVAILABLE.value
    assert "without weather assumptions" in body["notice"]


def test_weather_endpoint_validates_coordinates_and_date() -> None:
    invalid_coordinates = client.post(
        "/weather/forecast",
        json={**REQUEST, "coordinates": {"latitude": 91, "longitude": -79}},
    )
    invalid_date = client.post(
        "/weather/forecast",
        json={**REQUEST, "forecast_date": "not-a-date"},
    )

    assert invalid_coordinates.status_code == 422
    assert invalid_date.status_code == 422
