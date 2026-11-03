"""OpenAI Agents SDK tool for source-aware daily forecasts."""

import asyncio
from collections.abc import Callable
from datetime import date
from typing import Annotated

from agents import FunctionTool, function_tool
from pydantic import Field

from app.domain.schemas import (
    GeoCoordinates,
    WeatherForecastRequest,
    WeatherForecastResponse,
)
from app.providers.factory import get_weather_provider
from app.providers.weather import WeatherProvider
from app.services.weather import get_weather_forecast


def create_weather_forecast_tool(
    provider_factory: Callable[[], WeatherProvider] = get_weather_provider,
) -> FunctionTool:
    @function_tool(
        name_override="get_weather_forecast",
        description_override=(
            "Look up a sourced daily forecast for coordinates and a travel date. Forecasts "
            "may be unavailable outside provider coverage; never infer weather when unavailable."
        ),
        output_type=WeatherForecastResponse,
    )
    async def weather_forecast(
        latitude: Annotated[float, Field(ge=-90, le=90)],
        longitude: Annotated[float, Field(ge=-180, le=180)],
        forecast_date: date,
    ) -> WeatherForecastResponse:
        request = WeatherForecastRequest(
            coordinates=GeoCoordinates(latitude=latitude, longitude=longitude),
            forecast_date=forecast_date,
        )
        provider = provider_factory()
        return await asyncio.to_thread(get_weather_forecast, provider, request)

    return weather_forecast
