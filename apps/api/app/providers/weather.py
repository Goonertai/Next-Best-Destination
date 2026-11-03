"""Open-Meteo forecast provider boundary."""

from datetime import UTC, datetime
from math import isfinite
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.domain.schemas import (
    DailyWeatherForecast,
    PlaceDataStatus,
    PlaceSource,
    WeatherForecastRequest,
)
from app.providers.errors import ProviderRequestError

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_DOCS_URL = "https://open-meteo.com/en/docs"


class WeatherProvider(Protocol):
    data_status: PlaceDataStatus

    def get_daily_forecast(self, request: WeatherForecastRequest) -> DailyWeatherForecast:
        """Return a sourced daily forecast, or raise if one is unavailable."""


class OpenMeteoWeatherProvider:
    """Fetch a daily forecast without credentials for non-commercial use."""

    data_status = PlaceDataStatus.LIVE

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def get_daily_forecast(self, request: WeatherForecastRequest) -> DailyWeatherForecast:
        response_body = self._request(
            params={
                "latitude": request.coordinates.latitude,
                "longitude": request.coordinates.longitude,
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "temperature_unit": "celsius",
                "timezone": "auto",
                "start_date": request.forecast_date.isoformat(),
                "end_date": request.forecast_date.isoformat(),
                "forecast_days": 16,
            }
        )
        daily = response_body.get("daily")
        timezone = response_body.get("timezone")
        if not isinstance(daily, dict) or not isinstance(timezone, str):
            raise ProviderRequestError("Weather provider returned an invalid response.")

        dates = daily.get("time")
        if not isinstance(dates, list) or request.forecast_date.isoformat() not in dates:
            raise ProviderRequestError("Weather provider has no forecast for that date.")
        index = dates.index(request.forecast_date.isoformat())

        try:
            forecast = DailyWeatherForecast(
                forecast_date=request.forecast_date,
                timezone=timezone,
                weather_code=_integer_at(daily, "weather_code", index),
                temperature_max_c=_number_at(daily, "temperature_2m_max", index),
                temperature_min_c=_number_at(daily, "temperature_2m_min", index),
                precipitation_probability_max_pct=_optional_integer_at(
                    daily,
                    "precipitation_probability_max",
                    index,
                ),
                source=PlaceSource(
                    provider="Open-Meteo Forecast API",
                    url=OPEN_METEO_DOCS_URL,
                    retrieved_at=datetime.now(UTC),
                ),
                data_status=PlaceDataStatus.LIVE,
            )
        except (IndexError, TypeError, ValueError, ValidationError) as exc:
            raise ProviderRequestError(
                "Weather provider returned incomplete forecast data."
            ) from exc
        return forecast

    def _request(self, *, params: dict[str, str | float | int]) -> dict[str, object]:
        client = self._client or httpx.Client(timeout=8.0)
        close_client = self._client is None
        try:
            response = client.get(OPEN_METEO_FORECAST_URL, params=params)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ProviderRequestError("Weather provider returned an invalid response.")
            return body
        except ProviderRequestError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderRequestError("Weather provider request failed.") from exc
        finally:
            if close_client:
                client.close()


def _number_at(values: dict[str, object], key: str, index: int) -> float:
    series = values.get(key)
    if not isinstance(series, list):
        raise ValueError(f"missing daily series: {key}")
    value = series[index]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid numeric value: {key}")
    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise ValueError(f"invalid numeric value: {key}")
    return numeric_value


def _integer_at(values: dict[str, object], key: str, index: int) -> int:
    value = _number_at(values, key, index)
    if not value.is_integer():
        raise ValueError(f"invalid integer value: {key}")
    return int(value)


def _optional_integer_at(values: dict[str, object], key: str, index: int) -> int | None:
    series = values.get(key)
    if not isinstance(series, list):
        raise ValueError(f"missing daily series: {key}")
    value = series[index]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid integer value: {key}")
    number = float(value)
    if not number.is_integer():
        raise ValueError(f"invalid integer value: {key}")
    return int(number)
