from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validate_preferences_returns_validated_input_only() -> None:
    response = client.post(
        "/itineraries/validate",
        json={
            "destination": "Montreal",
            "start_date": "2026-11-10",
            "end_date": "2026-11-13",
            "total_budget": "1500.00",
            "currency": "CAD",
            "travelers": 2,
            "interests": ["Food", "History"],
            "preferences": "",
            "pace": "balanced",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "valid"
    assert body["itinerary_generated"] is False
    assert body["preferences"]["destination"] == "Montreal"


def test_validate_preferences_returns_422_for_invalid_dates() -> None:
    response = client.post(
        "/itineraries/validate",
        json={
            "destination": "Montreal",
            "start_date": "2026-11-13",
            "end_date": "2026-11-10",
            "total_budget": "1500.00",
            "currency": "CAD",
            "travelers": 2,
            "interests": ["Food"],
            "preferences": "",
            "pace": "balanced",
        },
    )

    assert response.status_code == 422
