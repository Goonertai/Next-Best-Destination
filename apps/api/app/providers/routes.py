"""Google Routes API provider boundary."""

import re
from datetime import UTC, datetime
from math import ceil
from typing import Protocol

import httpx

from app.domain.schemas import (
    PlaceDataStatus,
    PlaceSource,
    RouteEstimate,
    RouteEstimateRequest,
)
from app.providers.errors import ProviderRequestError, RouteNotFoundError

ROUTES_COMPUTE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUTES_FIELD_MASK = "routes.duration,routes.distanceMeters"
ROUTES_SOURCE_URL = "https://developers.google.com/maps/documentation/routes"
_DURATION_SECONDS = re.compile(r"^(\d+(?:\.\d+)?)s$")


class RoutesProvider(Protocol):
    def compute_route(self, request: RouteEstimateRequest) -> RouteEstimate:
        """Return a sourced duration and distance estimate."""


class GoogleRoutesProvider:
    """Server-side client for Routes API Compute Routes."""

    data_status = PlaceDataStatus.LIVE

    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self._client = client

    def compute_route(self, request: RouteEstimateRequest) -> RouteEstimate:
        payload = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": request.origin.latitude,
                        "longitude": request.origin.longitude,
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": request.destination.latitude,
                        "longitude": request.destination.longitude,
                    }
                }
            },
            "travelMode": request.mode.value,
        }
        client = self._client or httpx.Client(timeout=8.0)
        close_client = self._client is None
        try:
            response = client.post(
                ROUTES_COMPUTE_URL,
                headers={
                    "X-Goog-Api-Key": self.api_key,
                    "X-Goog-FieldMask": ROUTES_FIELD_MASK,
                },
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderRequestError("Routes API request failed.") from exc
        finally:
            if close_client:
                client.close()

        if not isinstance(body, dict):
            raise ProviderRequestError("Routes API returned an invalid response.")
        routes = body.get("routes")
        if not isinstance(routes, list) or not routes:
            raise RouteNotFoundError("No route was returned for these coordinates.")
        route = routes[0]
        if not isinstance(route, dict):
            raise ProviderRequestError("Routes API returned an invalid route.")
        duration = route.get("duration")
        distance_meters = route.get("distanceMeters")
        duration_match = (
            _DURATION_SECONDS.fullmatch(duration) if isinstance(duration, str) else None
        )
        if (
            duration_match is None
            or isinstance(distance_meters, bool)
            or not isinstance(distance_meters, (int, float))
        ):
            raise ProviderRequestError("Routes API response did not include duration and distance.")

        seconds = float(duration_match.group(1))
        return RouteEstimate(
            duration_minutes=max(1, ceil(seconds / 60)),
            distance_meters=round(distance_meters),
            mode=request.mode,
            source=PlaceSource(
                provider="Google Routes API",
                url=ROUTES_SOURCE_URL,
                retrieved_at=datetime.now(UTC),
            ),
            data_status=PlaceDataStatus.LIVE,
        )
