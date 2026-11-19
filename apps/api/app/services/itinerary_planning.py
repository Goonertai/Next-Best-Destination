"""Compose sourced provider records into a practical, editable trip plan."""

from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta

from app.domain.schemas import (
    Activity,
    GeoCoordinates,
    Itinerary,
    ItineraryDay,
    ItineraryPlanRequest,
    PlaceDataStatus,
    PlaceReference,
    PlaceValidationRequest,
    RouteEstimateRequest,
    RouteMode,
    TravelTimeEstimate,
    WeatherForecastRequest,
)
from app.providers.demo import DemoPlacesProvider, DemoRoutesProvider, DemoWeatherProvider
from app.providers.errors import (
    ProviderNotConfiguredError,
    ProviderRequestError,
    RouteNotFoundError,
)
from app.providers.factory import (
    get_places_provider,
    get_routes_provider,
    get_weather_provider,
)
from app.providers.places import PlacesProvider
from app.providers.routes import RoutesProvider
from app.providers.weather import WeatherProvider
from app.services.places import group_places_geographically, validate_place_reference
from app.services.weather import get_weather_forecast


class ItineraryPlanner:
    """Fetch current place data and schedule only provider-validated venues.

    The sample mode uses fictional fixtures, visibly marked as mock. Live mode
    requires Google credentials and never falls back to synthetic records.
    """

    def __init__(
        self,
        *,
        live_places_factory: Callable[[], PlacesProvider] = get_places_provider,
        live_routes_factory: Callable[[], RoutesProvider] = get_routes_provider,
        live_weather_factory: Callable[[], WeatherProvider] = get_weather_provider,
    ) -> None:
        self._live_places_factory = live_places_factory
        self._live_routes_factory = live_routes_factory
        self._live_weather_factory = live_weather_factory

    def plan(self, request: ItineraryPlanRequest) -> Itinerary:
        if request.data_mode == "demo":
            places: PlacesProvider = DemoPlacesProvider()
            routes: RoutesProvider = DemoRoutesProvider()
            weather: WeatherProvider = DemoWeatherProvider()
        else:
            places = self._live_places_factory()
            routes = self._live_routes_factory()
            weather = self._live_weather_factory()
        return build_itinerary(request, places=places, routes=routes, weather=weather)


def build_itinerary(
    request: ItineraryPlanRequest,
    *,
    places: PlacesProvider,
    routes: RoutesProvider,
    weather: WeatherProvider,
) -> Itinerary:
    attractions_query = f"{', '.join(request.interests[:3])} attractions in {request.destination}"
    restaurants_query = f"restaurants in {request.destination}"
    if request.preferences.strip():
        restaurants_query = (
            f"{request.preferences.strip()[:180]} restaurants in {request.destination}"
        )

    attraction_results = places.search_text(attractions_query, page_size=20)
    restaurant_results = places.search_text(restaurants_query, page_size=20)
    warnings: list[str] = []
    warnings.append(
        f"The {request.currency} budget was recorded but not validated because "
        "no price data is available."
    )
    raw_by_id = {place.place_id: place for place in [*attraction_results, *restaurant_results]}
    attraction_ids = {place.place_id for place in attraction_results}
    restaurant_ids = {place.place_id for place in restaurant_results}
    restaurant_ids -= attraction_ids
    raw_groups = group_places_geographically(list(raw_by_id.values()))
    area_pools = [
        {
            "area_id": group.area_id,
            "attractions": [place for place in group.places if place.place_id in attraction_ids],
            "restaurants": [place for place in group.places if place.place_id in restaurant_ids],
        }
        for group in raw_groups
    ]

    pace_slots = {
        "relaxed": [("attractions", 9), ("restaurants", 12)],
        "balanced": [("attractions", 9), ("restaurants", 12), ("attractions", 15)],
        "packed": [
            ("attractions", 9),
            ("restaurants", 12),
            ("attractions", 15),
            ("attractions", 18),
        ],
    }[request.pace.value]
    number_of_days = (request.end_date - request.start_date).days
    total_attractions = sum(len(area["attractions"]) for area in area_pools)
    scheduled_days = []

    for day_offset in range(number_of_days):
        travel_date = request.start_date + timedelta(days=day_offset)
        active_areas = [area for area in area_pools if area["attractions"] or area["restaurants"]]
        selected_area = max(
            active_areas,
            key=lambda area: len(area["attractions"]) + len(area["restaurants"]),
            default=None,
        )
        selected = []
        if selected_area is not None:
            for category, hour in pace_slots:
                pool = selected_area[category]
                if pool:
                    selected.append((pool.pop(0), category, hour))
        scheduled_days.append(
            (
                travel_date,
                selected_area["area_id"] if selected_area and selected else None,
                selected,
            )
        )

    # Place Details calls are made only for venues that will actually appear in
    # the itinerary; unused search results are not individually validated.
    selected_candidates = {
        place.place_id: place for _, _, selected in scheduled_days for place, _, _ in selected
    }
    validated_by_id = {}
    for candidate in selected_candidates.values():
        try:
            result = validate_place_reference(
                places,
                PlaceValidationRequest(
                    place_id=candidate.place_id,
                    coordinates=GeoCoordinates(
                        latitude=candidate.latitude,
                        longitude=candidate.longitude,
                    ),
                ),
            )
        except ProviderRequestError:
            warnings.append(f"Skipped place {candidate.place_id}: provider validation failed.")
            continue
        if result.is_valid and result.place is not None:
            validated_by_id[result.place.place_id] = result.place
        else:
            warnings.append(f"Skipped place {candidate.place_id}: provider validation failed.")

    trip_days: list[ItineraryDay] = []
    for travel_date, day_area, selected in scheduled_days:
        verified_selection = [
            (validated_by_id[place.place_id], category, hour)
            for place, category, hour in selected
            if place.place_id in validated_by_id
        ]
        activities: list[Activity] = []
        prior_place = None
        for place, category, hour in verified_selection:
            route_time = None
            if prior_place is not None:
                try:
                    estimate = routes.compute_route(
                        RouteEstimateRequest(
                            origin=GeoCoordinates(
                                latitude=prior_place.latitude,
                                longitude=prior_place.longitude,
                            ),
                            destination=GeoCoordinates(
                                latitude=place.latitude,
                                longitude=place.longitude,
                            ),
                            mode=RouteMode.WALK,
                        )
                    )
                    route_time = TravelTimeEstimate(
                        minutes=estimate.duration_minutes,
                        mode=estimate.mode.value,
                        is_estimate=True,
                        source=estimate.source,
                    )
                except (
                    ProviderNotConfiguredError,
                    ProviderRequestError,
                    RouteNotFoundError,
                ) as exc:
                    warnings.append(f"Route estimate unavailable: {exc}")

            activities.append(
                Activity(
                    start_time=datetime.combine(travel_date, time(hour=hour)),
                    end_time=datetime.combine(travel_date, time(hour=hour + 1)),
                    category=category[:-1] if category.endswith("s") else category,
                    place=PlaceReference(
                        name=place.name,
                        place_id=place.place_id,
                        latitude=place.latitude,
                        longitude=place.longitude,
                        source=place.source,
                    ),
                    description=(
                        "Retrieved from the selected category search. "
                        "Check the source for current details."
                    ),
                    place_is_verified=(place.data_status == PlaceDataStatus.LIVE),
                    data_status=place.data_status,
                    travel_from_previous=route_time,
                )
            )
            prior_place = place

        day_weather = None
        if activities:
            coordinates = GeoCoordinates(
                latitude=activities[0].place.latitude,
                longitude=activities[0].place.longitude,
            )
            result = get_weather_forecast(
                weather,
                WeatherForecastRequest(coordinates=coordinates, forecast_date=travel_date),
            )
            day_weather = result.forecast
            if result.forecast is None:
                warnings.append(f"Weather unavailable for {travel_date.isoformat()}.")

        trip_days.append(
            ItineraryDay(
                date=travel_date,
                activities=activities,
                weather=day_weather,
                area_id=day_area if activities else None,
            )
        )

    if not validated_by_id:
        warnings.append("No provider-validated places were returned; no venue was added.")
    if total_attractions < number_of_days:
        warnings.append(
            "Some days may have fewer activities because the provider returned few attractions."
        )

    data_status = PlaceDataStatus.MOCK if request.data_mode == "demo" else PlaceDataStatus.LIVE
    notice = (
        "Sample plan only. Venues, coordinates, routes, and weather are fictional synthetic "
        "fixtures; none are real or verified."
        if request.data_mode == "demo"
        else (
            "Every included place was checked against Google Places. Scheduled times are "
            "planning placeholders, not verified opening hours. Route durations are estimates; "
            "weather is forecast data. Prices are unavailable from these sources."
        )
    )
    return Itinerary(
        destination=request.destination,
        currency=request.currency,
        days=trip_days,
        generated_at=datetime.now(UTC),
        generation_mode=request.data_mode,
        data_status=data_status,
        notice=notice,
        warnings=list(dict.fromkeys(warnings)),
    )
