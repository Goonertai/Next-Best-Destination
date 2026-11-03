from datetime import date

import httpx
import pytest

from app.domain.schemas import GeoCoordinates, PlaceDataStatus, WeatherForecastRequest
from app.providers.errors import ProviderRequestError
from app.providers.weather import (
    OPEN_METEO_DOCS_URL,
    OpenMeteoWeatherProvider,
)

TRAVEL_DATE = date(2026, 11, 10)


def weather_request() -> WeatherForecastRequest:
    return WeatherForecastRequest(
        coordinates=GeoCoordinates(latitude=43.6532, longitude=-79.3832),
        forecast_date=TRAVEL_DATE,
    )


def weather_payload() -> dict[str, object]:
    return {
        "timezone": "America/Toronto",
        "daily": {
            "time": ["2026-11-10"],
            "weather_code": [3],
            "temperature_2m_max": [12.5],
            "temperature_2m_min": [4.2],
            "precipitation_probability_max": [30],
        },
    }


def test_forecast_request_returns_sourced_daily_values_in_celsius() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.open-meteo.com"
        assert request.url.path == "/v1/forecast"
        assert request.url.params["latitude"] == "43.6532"
        assert request.url.params["longitude"] == "-79.3832"
        assert request.url.params["temperature_unit"] == "celsius"
        assert request.url.params["timezone"] == "auto"
        assert request.url.params["start_date"] == TRAVEL_DATE.isoformat()
        assert request.url.params["end_date"] == TRAVEL_DATE.isoformat()
        assert "precipitation_probability_max" in request.url.params["daily"]
        return httpx.Response(200, json=weather_payload())

    client = httpx.Client(transport=httpx.MockTransport(handle))
    forecast = OpenMeteoWeatherProvider(client).get_daily_forecast(weather_request())

    assert forecast.forecast_date == TRAVEL_DATE
    assert forecast.timezone == "America/Toronto"
    assert forecast.weather_code == 3
    assert forecast.temperature_max_c == 12.5
    assert forecast.temperature_min_c == 4.2
    assert forecast.precipitation_probability_max_pct == 30
    assert forecast.data_status == PlaceDataStatus.LIVE
    assert forecast.source.provider == "Open-Meteo Forecast API"
    assert forecast.source.url == OPEN_METEO_DOCS_URL
    assert forecast.source.retrieved_at.tzinfo is not None
    client.close()


def test_forecast_with_no_returned_date_fails_without_inventing_values() -> None:
    payload = weather_payload()
    payload["daily"] = {**payload["daily"], "time": ["2026-11-11"]}
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    )

    with pytest.raises(ProviderRequestError, match="no forecast for that date"):
        OpenMeteoWeatherProvider(client).get_daily_forecast(weather_request())
    client.close()


def test_http_failure_is_converted_to_safe_provider_error() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(503, text="synthetic private upstream details")
        )
    )

    with pytest.raises(ProviderRequestError, match="Weather provider request failed") as error:
        OpenMeteoWeatherProvider(client).get_daily_forecast(weather_request())

    assert "synthetic private" not in str(error.value)
    client.close()


def test_invalid_temperature_series_is_rejected() -> None:
    payload = weather_payload()
    payload["daily"] = {**payload["daily"], "temperature_2m_max": [None]}
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    )

    with pytest.raises(ProviderRequestError, match="incomplete forecast data"):
        OpenMeteoWeatherProvider(client).get_daily_forecast(weather_request())
    client.close()
