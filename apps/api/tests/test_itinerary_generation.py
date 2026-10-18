from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PREFERENCES = {
    "destination": "Montreal",
    "start_date": "2026-11-10",
    "end_date": "2026-11-13",
    "total_budget": "1500.00",
    "currency": "CAD",
    "travelers": 2,
    "interests": ["Food", "History"],
    "preferences": "Keep the pace relaxed",
    "pace": "relaxed",
}


def test_generate_returns_dated_demo_suggestions_without_fabricated_places() -> None:
    response = client.post("/itineraries/generate", json=PREFERENCES)

    assert response.status_code == 200
    body = response.json()
    assert body["generation_mode"] == "demo"
    assert body["is_complete_itinerary"] is False
    assert body["uses_verified_place_data"] is False
    assert "no specific venues" in body["notice"]
    assert [day["date"] for day in body["days"]] == [
        "2026-11-10",
        "2026-11-11",
        "2026-11-12",
    ]
    assert "food-focused" in body["days"][0]["suggestions"][0]
    assert "history-focused" in body["days"][0]["suggestions"][1]
    assert "place_id" not in body["days"][0]
    assert "estimated_cost" not in body["days"][0]


def test_generate_rejects_invalid_preferences() -> None:
    payload = {**PREFERENCES, "travelers": 0}

    response = client.post("/itineraries/generate", json=payload)

    assert response.status_code == 422


def test_demo_generator_output_is_deterministic() -> None:
    first = client.post("/itineraries/generate", json=PREFERENCES).json()
    second = client.post("/itineraries/generate", json=PREFERENCES).json()

    assert first == second
