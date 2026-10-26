"""Travel-agent tools with typed, explicitly non-verified demo outputs."""

from typing import Annotated, Literal

from agents import Agent, FunctionTool, function_tool
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agent.maps_tools import (
    create_place_search_tool,
    create_place_validation_tool,
    create_route_estimate_tool,
)


class ActivityIdeasRequest(BaseModel):
    """Inputs for generic interest prompts; not a real place search."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    destination: Annotated[str, Field(min_length=1, max_length=160)]
    interests: Annotated[list[str], Field(min_length=1, max_length=20)]

    @field_validator("interests")
    @classmethod
    def interests_must_not_be_blank(cls, interests: list[str]) -> list[str]:
        cleaned = [interest.strip() for interest in interests]
        if any(not interest for interest in cleaned):
            raise ValueError("interests must not contain blank values")
        return cleaned


class ActivityIdea(BaseModel):
    interest: str
    prompt: str


class ActivityIdeasResult(BaseModel):
    """Structured generic suggestions with an explicit no-retrieval status."""

    destination: str
    ideas: list[ActivityIdea]
    data_status: Literal["not_retrieved"] = "not_retrieved"
    notice: str = (
        "Generic planning prompts only. No venues or other travel facts were searched or verified."
    )


def suggest_activity_ideas(request: ActivityIdeasRequest) -> ActivityIdeasResult:
    """Create deterministic generic prompts without inventing venues or travel facts."""
    return ActivityIdeasResult(
        destination=request.destination,
        ideas=[
            ActivityIdea(
                interest=interest,
                prompt=(
                    f"Consider a {interest.lower()}-focused activity in {request.destination}. "
                    "Choose a specific venue only after checking a current source."
                ),
            )
            for interest in request.interests
        ],
    )


def create_activity_ideas_tool() -> FunctionTool:
    """Build the SDK tool with generated input and strict Pydantic output schemas."""

    @function_tool(
        name_override="suggest_activity_ideas",
        description_override=(
            "Return generic activity prompts for traveler interests. This tool does not search "
            "for, or verify, specific places or travel facts."
        ),
        output_type=ActivityIdeasResult,
    )
    async def activity_ideas(
        destination: Annotated[str, Field(min_length=1, max_length=160)],
        interests: Annotated[list[str], Field(min_length=1, max_length=20)],
    ) -> ActivityIdeasResult:
        """Suggest general activity themes without returning venue claims."""
        request = ActivityIdeasRequest(destination=destination, interests=interests)
        return suggest_activity_ideas(request)

    return activity_ideas


def build_travel_agent() -> Agent:
    """Create an SDK agent; constructing it does not make a model/API request."""
    return Agent(
        name="Travel Planning Assistant",
        instructions=(
            "Help organize travel plans. Use activity prompts only as generic ideas. Never claim "
            "that a venue, price, opening hour, availability, weather, or travel time was verified "
            "unless a dedicated data tool returns source information. Label estimates clearly."
        ),
        tools=[
            create_activity_ideas_tool(),
            create_place_search_tool("attractions"),
            create_place_search_tool("restaurants"),
            create_place_validation_tool(),
            create_route_estimate_tool(),
        ],
    )
