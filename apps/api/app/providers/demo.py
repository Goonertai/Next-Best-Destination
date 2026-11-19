"""Synthetic providers for the interactive sample mode.

These deliberately fictional records make the product flow usable without API
credentials. They must remain visibly marked as mock and must never be presented
as real venues, weather, costs, or travel times.
"""

from datetime import UTC, datetime

from app.domain.schemas import (
    DailyWeatherForecast,
    PlaceDataStatus,
    PlaceRecord,
    PlaceSource,
    RouteEstimate,
    RouteEstimateRequest,
    WeatherForecastRequest,
)


def _source(name: str) -> PlaceSource:
    return PlaceSource(
        provider="Synthetic demo fixture (not real travel data)",
        url=f"https://example.test/demo/{name}",
        retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class DemoPlacesProvider:
    data_status = PlaceDataStatus.MOCK

    def __init__(self) -> None:
        self._places = [
            PlaceRecord(
                name=f"Sample attraction {index} (fictional)",
                place_id=f"demo-attraction-{index}",
                latitude=1.0 + index * 0.0003,
                longitude=2.0 + index * 0.0003,
                formatted_address="Synthetic sample location; not a real address",
                primary_type="demo_fixture",
                source=_source(f"attraction-{index}"),
                data_status=PlaceDataStatus.MOCK,
            )
            for index in range(1, 9)
        ] + [
            PlaceRecord(
                name=f"Sample restaurant {index} (fictional)",
                place_id=f"demo-restaurant-{index}",
                latitude=1.001 + index * 0.0003,
                longitude=2.001 + index * 0.0003,
                formatted_address="Synthetic sample location; not a real address",
                primary_type="demo_fixture",
                source=_source(f"restaurant-{index}"),
                data_status=PlaceDataStatus.MOCK,
            )
            for index in range(1, 5)
        ]

    def search_text(self, query: str, page_size: int = 10) -> list[PlaceRecord]:
        category = "restaurant" if "restaurant" in query.lower() else "attraction"
        return [place for place in self._places if category in place.place_id][:page_size]

    def get_place(self, place_id: str) -> PlaceRecord | None:
        return next((place for place in self._places if place.place_id == place_id), None)


class DemoRoutesProvider:
    data_status = PlaceDataStatus.MOCK

    def compute_route(self, request: RouteEstimateRequest) -> RouteEstimate:
        return RouteEstimate(
            duration_minutes=12,
            distance_meters=900,
            mode=request.mode,
            source=_source("route"),
            data_status=PlaceDataStatus.MOCK,
            notice="Synthetic route fixture only; not a real travel-time estimate.",
        )


class DemoWeatherProvider:
    data_status = PlaceDataStatus.MOCK

    def get_daily_forecast(self, request: WeatherForecastRequest) -> DailyWeatherForecast:
        return DailyWeatherForecast(
            forecast_date=request.forecast_date,
            timezone="Demo/Fixture",
            weather_code=3,
            temperature_max_c=18,
            temperature_min_c=11,
            precipitation_probability_max_pct=25,
            source=_source("weather"),
            data_status=PlaceDataStatus.MOCK,
        )
