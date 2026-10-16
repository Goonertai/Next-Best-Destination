from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.domain.schemas import (
    Estimate,
    PlaceReference,
    PlaceSource,
    TravelPreferences,
    TravelTimeEstimate,
)


def valid_preferences() -> dict[str, object]:
    return {
        "destination": "Montreal",
        "start_date": "2026-11-10",
        "end_date": "2026-11-13",
        "total_budget": "1500.00",
        "currency": "CAD",
        "travelers": 2,
        "interests": ["Food", "History"],
        "preferences": "",
        "pace": "balanced",
    }


def test_preferences_normalize_and_parse() -> None:
    preferences = TravelPreferences.model_validate(valid_preferences())

    assert preferences.destination == "Montreal"
    assert preferences.start_date == date(2026, 11, 10)
    assert str(preferences.total_budget) == "1500.00"
    assert preferences.pace == "balanced"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("end_date", "2026-11-10"),
        ("currency", "dollars"),
        ("travelers", 0),
        ("interests", ["Food", " "]),
        ("unexpected", "not allowed"),
    ],
)
def test_preferences_reject_invalid_values(field: str, value: object) -> None:
    payload = valid_preferences()
    payload[field] = value

    with pytest.raises(ValidationError):
        TravelPreferences.model_validate(payload)


def test_place_reference_requires_source_and_bounded_coordinates() -> None:
    payload = {
        "name": "Example Place",
        "place_id": "provider-place-id",
        "latitude": 45.5,
        "longitude": -73.6,
        "source": {
            "provider": "fixture",
            "url": "https://example.invalid/place",
            "retrieved_at": datetime.now(UTC).isoformat(),
        },
    }
    place = PlaceReference.model_validate(payload)
    assert place.latitude == 45.5

    payload["latitude"] = 100
    with pytest.raises(ValidationError):
        PlaceReference.model_validate(payload)


def test_estimates_must_be_explicitly_labeled_and_sourced() -> None:
    with pytest.raises(ValidationError):
        Estimate(amount="10", currency="CAD", is_estimate=False)

    with pytest.raises(ValidationError):
        TravelTimeEstimate(minutes=15, mode="walking", is_estimate=True)

    source = PlaceSource(
        provider="fixture",
        url="https://example.invalid/route",
        retrieved_at=datetime.now(UTC),
    )
    estimate = TravelTimeEstimate(minutes=15, mode="walking", is_estimate=True, source=source)
    assert estimate.minutes == 15
