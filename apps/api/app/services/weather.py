"""Weather lookup use case with an explicit unavailable fallback."""

from app.domain.schemas import (
    PlaceDataStatus,
    WeatherForecastRequest,
    WeatherForecastResponse,
)
from app.providers.errors import ProviderRequestError
from app.providers.weather import WeatherProvider


def get_weather_forecast(
    provider: WeatherProvider,
    request: WeatherForecastRequest,
) -> WeatherForecastResponse:
    try:
        forecast = provider.get_daily_forecast(request)
    except ProviderRequestError:
        return WeatherForecastResponse(
            forecast=None,
            data_status=PlaceDataStatus.UNAVAILABLE,
            notice=(
                "Weather forecast unavailable for this date or location. Continue planning "
                "without weather assumptions."
            ),
        )

    if forecast.data_status == PlaceDataStatus.MOCK:
        notice = "Mock fixture forecast only; it is not current or real weather data."
    else:
        notice = "Forecast conditions are estimates and may change; check again near travel."
    return WeatherForecastResponse(
        forecast=forecast,
        data_status=forecast.data_status,
        notice=notice,
    )
