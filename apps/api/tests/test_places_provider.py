import httpx
import pytest

from app.domain.schemas import PlaceDataStatus
from app.providers.errors import ProviderRequestError
from app.providers.places import (
    PLACES_DETAILS_FIELD_MASK,
    PLACES_SEARCH_FIELD_MASK,
    GooglePlacesProvider,
)


def google_place(place_id: str = "fake-place-id") -> dict[str, object]:
    return {
        "id": place_id,
        "displayName": {"text": "Fixture Cafe"},
        "formattedAddress": "Fixture address",
        "location": {"latitude": 1.25, "longitude": 2.5},
        "primaryType": "cafe",
        "googleMapsUri": "https://maps.google.com/?q=fixture",
    }


def test_text_search_uses_places_new_field_mask_and_maps_sourced_results() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Goog-Api-Key"] == "test-key"
        assert request.headers["X-Goog-FieldMask"] == PLACES_SEARCH_FIELD_MASK
        assert request.url.path == "/v1/places:searchText"
        assert request.read() == b'{"textQuery":"restaurants in Fixture City","pageSize":3}'
        return httpx.Response(200, json={"places": [google_place()]})

    client = httpx.Client(transport=httpx.MockTransport(handle))
    provider = GooglePlacesProvider("test-key", client=client)

    results = provider.search_text("restaurants in Fixture City", page_size=3)

    assert len(results) == 1
    assert results[0].data_status == PlaceDataStatus.LIVE
    assert results[0].name == "Fixture Cafe"
    assert results[0].place_id == "fake-place-id"
    assert results[0].latitude == 1.25
    assert results[0].source.provider == "Google Places API (New)"
    assert results[0].source.retrieved_at.tzinfo is not None
    client.close()


def test_search_skips_results_without_valid_coordinates_or_identifiers() -> None:
    invalid_coordinates = {
        **google_place("bad-coordinates"),
        "location": {"latitude": 91, "longitude": 2},
    }
    no_identifier = {key: value for key, value in google_place().items() if key != "id"}
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={"places": [invalid_coordinates, no_identifier]},
            )
        )
    )

    assert GooglePlacesProvider("test-key", client).search_text("query", 5) == []
    client.close()


def test_place_details_uses_narrow_field_mask_and_returns_none_on_404() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Goog-FieldMask"] == PLACES_DETAILS_FIELD_MASK
        assert request.url.path.endswith("/missing-place")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handle))

    assert GooglePlacesProvider("test-key", client).get_place("missing-place") is None
    client.close()


def test_provider_converts_http_errors_to_safe_provider_errors() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(500, text="sensitive details"))
    )

    with pytest.raises(ProviderRequestError, match="Places API request failed"):
        GooglePlacesProvider("test-key", client).search_text("query", 5)
    client.close()
