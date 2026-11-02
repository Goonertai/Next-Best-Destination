"""Google Places API (New) provider boundary."""

from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from app.domain.schemas import GeoCoordinates, PlaceDataStatus, PlaceRecord, PlaceSource
from app.providers.errors import ProviderRequestError

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places"
PLACES_SEARCH_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.primaryType,places.googleMapsUri"
)
PLACES_DETAILS_FIELD_MASK = (
    "id,displayName,formattedAddress,location,primaryType,googleMapsUri,businessStatus"
)
PLACES_SOURCE_URL = "https://developers.google.com/maps/documentation/places/web-service"


class PlacesProvider(Protocol):
    data_status: PlaceDataStatus

    def search_text(self, query: str, page_size: int) -> list[PlaceRecord]:
        """Search current place listings for a text query."""

    def get_place(self, place_id: str) -> PlaceRecord | None:
        """Fetch a place by provider ID, or return ``None`` when it no longer exists."""


class GooglePlacesProvider:
    """Server-side client for Places Text Search and Place Details."""

    data_status = PlaceDataStatus.LIVE

    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self._client = client

    def search_text(self, query: str, page_size: int = 10) -> list[PlaceRecord]:
        payload = self._request(
            "POST",
            PLACES_TEXT_SEARCH_URL,
            headers={"X-Goog-FieldMask": PLACES_SEARCH_FIELD_MASK},
            json={"textQuery": query, "pageSize": page_size},
        )
        now = datetime.now(UTC)
        records: list[PlaceRecord] = []
        for raw_place in payload.get("places", []):
            record = self._to_record(raw_place, now)
            if record is not None:
                records.append(record)
        return records

    def get_place(self, place_id: str) -> PlaceRecord | None:
        encoded_id = quote(place_id, safe="")
        try:
            payload = self._request(
                "GET",
                f"{PLACES_DETAILS_URL}/{encoded_id}",
                headers={"X-Goog-FieldMask": PLACES_DETAILS_FIELD_MASK},
                allow_not_found=True,
            )
        except _PlaceNotFound:
            return None
        return self._to_record(payload, datetime.now(UTC))

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object] | None = None,
        allow_not_found: bool = False,
    ) -> dict[str, object]:
        request_headers = {"X-Goog-Api-Key": self.api_key, **headers}
        client = self._client or httpx.Client(timeout=8.0)
        close_client = self._client is None
        try:
            response = client.request(method, url, headers=request_headers, json=json)
            if allow_not_found and response.status_code == 404:
                raise _PlaceNotFound
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ProviderRequestError("Places API returned an invalid response.")
            return body
        except _PlaceNotFound:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderRequestError("Places API request failed.") from exc
        finally:
            if close_client:
                client.close()

    @staticmethod
    def _to_record(payload: dict[str, object], retrieved_at: datetime) -> PlaceRecord | None:
        place_id = payload.get("id")
        display_name = payload.get("displayName")
        location = payload.get("location")
        if not isinstance(place_id, str) or not isinstance(display_name, dict):
            return None
        if not isinstance(location, dict):
            return None
        name = display_name.get("text")
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        if (
            not isinstance(name, str)
            or isinstance(latitude, bool)
            or not isinstance(latitude, (int, float))
            or isinstance(longitude, bool)
            or not isinstance(longitude, (int, float))
        ):
            return None
        try:
            GeoCoordinates(latitude=latitude, longitude=longitude)
        except ValidationError:
            return None

        google_maps_uri = payload.get("googleMapsUri")
        source_url = (
            google_maps_uri
            if isinstance(google_maps_uri, str) and google_maps_uri.startswith("https://")
            else f"https://www.google.com/maps/search/?api=1&query_place_id={quote(place_id)}"
        )
        formatted_address = payload.get("formattedAddress")
        primary_type = payload.get("primaryType")
        return PlaceRecord(
            name=name,
            place_id=place_id,
            latitude=latitude,
            longitude=longitude,
            formatted_address=formatted_address if isinstance(formatted_address, str) else None,
            primary_type=primary_type if isinstance(primary_type, str) else None,
            google_maps_uri=google_maps_uri if isinstance(google_maps_uri, str) else None,
            source=PlaceSource(
                provider="Google Places API (New)",
                url=source_url,
                retrieved_at=retrieved_at,
            ),
            data_status=PlaceDataStatus.LIVE,
        )


class _PlaceNotFound(Exception):
    pass
