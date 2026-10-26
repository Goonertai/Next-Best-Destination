import httpx
import pytest

from app.domain.schemas import GeoCoordinates, PlaceDataStatus, RouteEstimateRequest, RouteMode
from app.providers.errors import ProviderRequestError, RouteNotFoundError
from app.providers.routes import ROUTES_FIELD_MASK, GoogleRoutesProvider


def route_request() -> RouteEstimateRequest:
    return RouteEstimateRequest(
        origin=GeoCoordinates(latitude=1.0, longitude=2.0),
        destination=GeoCoordinates(latitude=1.1, longitude=2.1),
        mode=RouteMode.WALK,
    )


def test_compute_routes_sends_field_mask_and_returns_sourced_estimate() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/directions/v2:computeRoutes"
        assert request.headers["X-Goog-Api-Key"] == "test-key"
        assert request.headers["X-Goog-FieldMask"] == ROUTES_FIELD_MASK
        assert b'"travelMode":"WALK"' in request.read()
        return httpx.Response(
            200,
            json={"routes": [{"duration": "455s", "distanceMeters": 1200}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handle))

    estimate = GoogleRoutesProvider("test-key", client).compute_route(route_request())

    assert estimate.duration_minutes == 8
    assert estimate.distance_meters == 1200
    assert estimate.is_estimate is True
    assert estimate.data_status == PlaceDataStatus.LIVE
    assert estimate.source.provider == "Google Routes API"
    client.close()


def test_compute_routes_reports_no_route_without_inventing_duration() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"routes": []}))
    )

    with pytest.raises(RouteNotFoundError):
        GoogleRoutesProvider("test-key", client).compute_route(route_request())
    client.close()


def test_compute_routes_hides_remote_error_body() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(403, text="private error"))
    )

    with pytest.raises(ProviderRequestError, match="Routes API request failed"):
        GoogleRoutesProvider("test-key", client).compute_route(route_request())
    client.close()
