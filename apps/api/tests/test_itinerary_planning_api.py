from fastapi.testclient import TestClient

from app.api.itineraries import get_itinerary_repository
from app.main import app
from app.repositories.itineraries import SqlAlchemyItineraryRepository

client = TestClient(app)

PLAN_REQUEST = {
    "destination": "Toronto",
    "start_date": "2026-12-10",
    "end_date": "2026-12-12",
    "total_budget": "1200.00",
    "currency": "CAD",
    "travelers": 2,
    "interests": ["History", "Food"],
    "preferences": "Vegetarian options",
    "pace": "balanced",
    "data_mode": "demo",
}


def test_demo_plan_contains_synthetic_places_sources_routes_and_weather() -> None:
    response = client.post("/itineraries/plan", json=PLAN_REQUEST)

    assert response.status_code == 200
    plan = response.json()
    assert plan["destination"] == "Toronto"
    assert plan["generation_mode"] == "demo"
    assert plan["data_status"] == "mock"
    assert "fictional" in plan["notice"]
    assert len(plan["days"]) == 2

    first_day = plan["days"][0]
    assert first_day["area_id"] == "area-1"
    assert len(first_day["activities"]) == 3
    assert first_day["activities"][0]["place"]["name"].endswith("(fictional)")
    assert first_day["activities"][0]["place"]["source"]["provider"].startswith(
        "Synthetic demo fixture"
    )
    assert first_day["activities"][0]["place_is_verified"] is False
    assert first_day["activities"][1]["travel_from_previous"]["is_estimate"] is True
    assert first_day["activities"][1]["data_status"] == "mock"
    assert first_day["weather"]["data_status"] == "mock"
    assert plan["total_estimated_cost"] is None


def test_live_plan_fails_clearly_without_google_credentials(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    request = {**PLAN_REQUEST, "data_mode": "live"}

    response = client.post("/itineraries/plan", json=request)

    assert response.status_code == 503
    assert "GOOGLE_MAPS_API_KEY" in response.json()["detail"]


def test_plan_rejects_trips_longer_than_30_days() -> None:
    response = client.post(
        "/itineraries/plan",
        json={**PLAN_REQUEST, "end_date": "2027-02-01"},
    )

    assert response.status_code == 422
    assert "trips cannot exceed 30 days" in str(response.json()["detail"])


def test_generated_itinerary_can_be_saved_listed_and_reopened(tmp_path) -> None:
    repository = SqlAlchemyItineraryRepository(f"sqlite:///{tmp_path / 'plans.db'}")
    app.dependency_overrides[get_itinerary_repository] = lambda: repository
    try:
        generated = client.post("/itineraries/plan", json=PLAN_REQUEST)
        saved_response = client.post("/itineraries/saved", json=generated.json())
        saved = saved_response.json()
        second_snapshot_response = client.post("/itineraries/saved", json=saved)
        second_snapshot = second_snapshot_response.json()

        assert generated.status_code == 200
        assert saved_response.status_code == 201
        assert saved["id"]
        assert second_snapshot["id"] != saved["id"]
        assert client.get("/itineraries/saved").json()[0]["id"] == second_snapshot["id"]
        assert client.get(f"/itineraries/{saved['id']}").json() == saved
        assert client.get("/itineraries/missing-id").status_code == 404
    finally:
        app.dependency_overrides.pop(get_itinerary_repository, None)


def test_sample_itinerary_supports_safe_remove_and_move_edits(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    plan = client.post("/itineraries/plan", json=PLAN_REQUEST).json()
    first_activity = plan["days"][0]["activities"][0]
    instruction = f"Remove {first_activity['place']['name']}"

    removed = client.post(
        "/itineraries/edit",
        json={"itinerary": plan, "instruction": instruction},
    )
    assert removed.status_code == 200
    assert removed.json()["edit_mode"] == "safe_rule"
    assert removed.json()["itinerary"]["id"] is None
    assert all(
        item["place"]["place_id"] != first_activity["place"]["place_id"]
        for day in removed.json()["itinerary"]["days"]
        for item in day["activities"]
    )
    assert removed.json()["itinerary"]["days"][0]["weather"] is None

    move_plan = client.post("/itineraries/plan", json=PLAN_REQUEST).json()
    moved_activity = move_plan["days"][0]["activities"][0]
    moved = client.post(
        "/itineraries/edit",
        json={
            "itinerary": move_plan,
            "instruction": f"Move {moved_activity['place']['name']} to day 2",
        },
    )
    assert moved.status_code == 200
    assert moved_activity["place"]["place_id"] not in {
        item["place"]["place_id"] for item in moved.json()["itinerary"]["days"][0]["activities"]
    }
    assert (
        moved.json()["itinerary"]["days"][1]["activities"][-1]["place"]["place_id"]
        == (moved_activity["place"]["place_id"])
    )


def test_sample_edit_rejects_ambiguous_or_unsupported_requests(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    plan = client.post("/itineraries/plan", json=PLAN_REQUEST).json()

    response = client.post(
        "/itineraries/edit",
        json={"itinerary": plan, "instruction": "Add a new popular place"},
    )

    assert response.status_code == 422
    assert "sample edits like" in response.json()["detail"]


def test_sample_edit_does_not_overbook_a_full_day(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    packed_plan = client.post(
        "/itineraries/plan",
        json={**PLAN_REQUEST, "pace": "packed"},
    ).json()
    activity = packed_plan["days"][0]["activities"][0]
    response = client.post(
        "/itineraries/edit",
        json={
            "itinerary": packed_plan,
            "instruction": f"Move {activity['place']['name']} to day 2",
        },
    )

    assert response.status_code == 422
    assert "already has four activities" in response.json()["detail"]
