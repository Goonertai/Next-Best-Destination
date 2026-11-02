"""OpenAI Agents SDK tools for sourced Google Maps data."""

import asyncio
from collections.abc import Callable
from typing import Annotated

from agents import FunctionTool, function_tool
from pydantic import Field

from app.domain.schemas import (
    GeoCoordinates,
    PlaceCategory,
    PlaceDataStatus,
    PlaceSearchResponse,
    PlaceValidationRequest,
    PlaceValidationResponse,
    RouteEstimateRequest,
    RouteMode,
    RouteToolResult,
)
from app.providers.errors import (
    ProviderNotConfiguredError,
    ProviderRequestError,
    RouteNotFoundError,
)
from app.providers.factory import get_places_provider, get_routes_provider
from app.providers.places import PlacesProvider
from app.providers.routes import RoutesProvider
from app.services.places import search_places, validate_place_reference


def create_place_search_tool(
    category: PlaceCategory,
    provider_factory: Callable[[], PlacesProvider] = get_places_provider,
) -> FunctionTool:
    tool_name = f"search_{category}"
    query_subject = "attractions" if category == "attractions" else "restaurants"

    @function_tool(
        name_override=tool_name,
        description_override=(
            f"Search current Google Places listings for {query_subject}. Return provider IDs, "
            "coordinates, and source metadata; never invent results."
        ),
        output_type=PlaceSearchResponse,
    )
    async def place_search(
        destination: Annotated[str, Field(min_length=1, max_length=160)],
        limit: Annotated[int, Field(ge=1, le=10)] = 5,
    ) -> PlaceSearchResponse:
        try:
            provider = provider_factory()
            return await asyncio.to_thread(
                search_places,
                provider,
                destination=destination,
                category=category,
                limit=limit,
            )
        except ProviderNotConfiguredError:
            return PlaceSearchResponse(
                destination=destination,
                category=category,
                results=[],
                data_status=PlaceDataStatus.UNAVAILABLE,
                notice="Google Maps credentials are not configured; no places were returned.",
            )
        except ProviderRequestError:
            return PlaceSearchResponse(
                destination=destination,
                category=category,
                results=[],
                data_status=PlaceDataStatus.UNAVAILABLE,
                notice="Google Places could not be reached; no places were returned.",
            )

    return place_search


def create_place_validation_tool(
    provider_factory: Callable[[], PlacesProvider] = get_places_provider,
) -> FunctionTool:
    @function_tool(
        name_override="validate_place_reference",
        description_override=(
            "Check a place ID against current Google Places details and compare supplied "
            "coordinates with the provider location."
        ),
        output_type=PlaceValidationResponse,
    )
    async def validate_place(
        place_id: Annotated[str, Field(min_length=1, max_length=256)],
        latitude: Annotated[float, Field(ge=-90, le=90)],
        longitude: Annotated[float, Field(ge=-180, le=180)],
    ) -> PlaceValidationResponse:
        request = PlaceValidationRequest(
            place_id=place_id,
            coordinates=GeoCoordinates(latitude=latitude, longitude=longitude),
        )
        try:
            provider = provider_factory()
            return await asyncio.to_thread(validate_place_reference, provider, request)
        except ProviderNotConfiguredError:
            return PlaceValidationResponse(
                is_valid=False,
                data_status=PlaceDataStatus.UNAVAILABLE,
                notice="Google Maps credentials are not configured; the place was not validated.",
            )
        except ProviderRequestError:
            return PlaceValidationResponse(
                is_valid=False,
                data_status=PlaceDataStatus.UNAVAILABLE,
                notice="Google Places could not be reached; the place was not validated.",
            )

    return validate_place


def create_route_estimate_tool(
    provider_factory: Callable[[], RoutesProvider] = get_routes_provider,
) -> FunctionTool:
    @function_tool(
        name_override="estimate_route",
        description_override=(
            "Estimate route duration and distance between coordinates using Google Routes. "
            "Always preserve the returned estimate label and source."
        ),
        output_type=RouteToolResult,
    )
    async def route_estimate(
        origin_latitude: Annotated[float, Field(ge=-90, le=90)],
        origin_longitude: Annotated[float, Field(ge=-180, le=180)],
        destination_latitude: Annotated[float, Field(ge=-90, le=90)],
        destination_longitude: Annotated[float, Field(ge=-180, le=180)],
        mode: RouteMode = RouteMode.DRIVE,
    ) -> RouteToolResult:
        request = RouteEstimateRequest(
            origin=GeoCoordinates(latitude=origin_latitude, longitude=origin_longitude),
            destination=GeoCoordinates(
                latitude=destination_latitude,
                longitude=destination_longitude,
            ),
            mode=mode,
        )
        try:
            provider = provider_factory()
            estimate = await asyncio.to_thread(provider.compute_route, request)
            return RouteToolResult(
                estimate=estimate,
                data_status=estimate.data_status,
                notice=estimate.notice,
            )
        except ProviderNotConfiguredError:
            return RouteToolResult(
                data_status=PlaceDataStatus.UNAVAILABLE,
                notice=(
                    "Google Maps credentials are not configured; no route estimate was returned."
                ),
            )
        except RouteNotFoundError:
            return RouteToolResult(
                data_status=PlaceDataStatus.LIVE,
                notice="Google Routes did not return a route for these coordinates.",
            )
        except ProviderRequestError:
            return RouteToolResult(
                data_status=PlaceDataStatus.UNAVAILABLE,
                notice="Google Routes could not be reached; no route estimate was returned.",
            )

    return route_estimate
