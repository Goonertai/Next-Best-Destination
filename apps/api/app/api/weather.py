"""HTTP endpoint for sourced daily weather forecasts."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.domain.schemas import WeatherForecastRequest, WeatherForecastResponse
from app.providers.factory import get_weather_provider as create_weather_provider
from app.providers.weather import WeatherProvider
from app.services.weather import get_weather_forecast

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_data_provider() -> WeatherProvider:
    return create_weather_provider()


@router.post("/forecast", response_model=WeatherForecastResponse)
def daily_weather_forecast(
    request: WeatherForecastRequest,
    provider: Annotated[WeatherProvider, Depends(get_weather_data_provider)],
) -> WeatherForecastResponse:
    return get_weather_forecast(provider, request)
