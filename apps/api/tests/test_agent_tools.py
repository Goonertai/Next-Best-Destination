from agents import FunctionTool
from fastapi.testclient import TestClient

from app.agent.tools import (
    ActivityIdeasRequest,
    build_travel_agent,
    create_activity_ideas_tool,
    suggest_activity_ideas,
)
from app.main import app

client = TestClient(app)


def test_activity_ideas_are_typed_deterministic_and_not_verified() -> None:
    request = ActivityIdeasRequest(destination="Montreal", interests=["Food", "History"])

    first = suggest_activity_ideas(request)
    second = suggest_activity_ideas(request)

    assert first == second
    assert first.model_dump() == {
        "destination": "Montreal",
        "ideas": [
            {
                "interest": "Food",
                "prompt": (
                    "Consider a food-focused activity in Montreal. Choose a specific venue "
                    "only after checking a current source."
                ),
            },
            {
                "interest": "History",
                "prompt": (
                    "Consider a history-focused activity in Montreal. Choose a specific venue "
                    "only after checking a current source."
                ),
            },
        ],
        "data_status": "not_retrieved",
        "notice": (
            "Generic planning prompts only. No venues or other travel facts were "
            "searched or verified."
        ),
    }


def test_sdk_tool_has_generated_input_and_structured_output_schemas() -> None:
    tool = create_activity_ideas_tool()

    assert isinstance(tool, FunctionTool)
    assert tool.name == "suggest_activity_ideas"
    assert tool.params_json_schema["required"] == ["destination", "interests"]
    assert tool.output_json_schema is not None
    assert "ideas" in tool.output_json_schema["properties"]
    assert "data_status" in tool.output_json_schema["properties"]


def test_travel_agent_registers_the_tool_without_running_a_model() -> None:
    agent = build_travel_agent()

    assert agent.name == "Travel Planning Assistant"
    assert [tool.name for tool in agent.tools] == ["suggest_activity_ideas"]


def test_activity_ideas_endpoint_returns_structured_non_verified_data() -> None:
    response = client.post(
        "/itineraries/activity-ideas",
        json={"destination": "Montreal", "interests": ["Food"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] == "not_retrieved"
    assert body["ideas"][0]["interest"] == "Food"
    assert "specific venue" in body["ideas"][0]["prompt"]
    assert "verified" in body["notice"]


def test_activity_ideas_endpoint_rejects_blank_interests() -> None:
    response = client.post(
        "/itineraries/activity-ideas",
        json={"destination": "Montreal", "interests": ["  "]},
    )

    assert response.status_code == 422
