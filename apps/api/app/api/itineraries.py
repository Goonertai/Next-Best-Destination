"""Endpoints for validating itinerary-generation inputs."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.agent.generation import DemoItineraryGenerator, ItineraryGenerator
from app.domain.schemas import (
    ItineraryDraft,
    PreferencesValidationResponse,
    TravelPreferences,
)

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


def get_itinerary_generator() -> ItineraryGenerator:
    """Provide the no-credential demo implementation until LLM setup is available."""
    return DemoItineraryGenerator()


@router.post("/validate", response_model=PreferencesValidationResponse)
def validate_preferences(
    preferences: TravelPreferences,
) -> PreferencesValidationResponse:
    """Validate and normalize trip preferences without generating a plan."""
    return PreferencesValidationResponse(preferences=preferences)


@router.post("/generate", response_model=ItineraryDraft)
def generate_demo_draft(
    preferences: TravelPreferences,
    generator: Annotated[ItineraryGenerator, Depends(get_itinerary_generator)],
) -> ItineraryDraft:
    """Return an explicitly incomplete, non-verified demo draft."""
    return generator.generate(preferences)
