"""Synthetic provider fixtures. These records are never real travel data."""

from datetime import UTC, datetime

from app.domain.schemas import (
    PlaceDataStatus,
    PlaceRecord,
    PlaceSource,
    RouteEstimate,
    RouteEstimateRequest,
)


def mock_place(place_id: str = "mock-place-1") -> PlaceRecord:
    return PlaceRecord(
        name="Mock Place (fixture only)",
        place_id=place_id,
        latitude=1.0,
        longitude=2.0,
        formatted_address="Synthetic test data",
        primary_type="mock_fixture",
        google_maps_uri=None,
        source=PlaceSource(
            provider="Mock fixture (not real place data)",
            url="https://example.test/mock-place",
            retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        data_status=PlaceDataStatus.MOCK,
    )


class MockPlacesProvider:
    data_status = PlaceDataStatus.MOCK

    def __init__(self) -> None:
        self.place = mock_place()
        self.queries: list[tuple[str, int]] = []

    def search_text(self, query: str, page_size: int = 10) -> list[PlaceRecord]:
        self.queries.append((query, page_size))
        return [self.place][:page_size]

    def get_place(self, place_id: str) -> PlaceRecord | None:
        return self.place if place_id == self.place.place_id else None


class MockRoutesProvider:
    data_status = PlaceDataStatus.MOCK

    def compute_route(self, request: RouteEstimateRequest) -> RouteEstimate:
        return RouteEstimate(
            duration_minutes=7,
            distance_meters=1200,
            mode=request.mode,
            source=mock_place().source,
            data_status=PlaceDataStatus.MOCK,
            notice="Synthetic route fixture only; not a real travel-time estimate.",
        )
