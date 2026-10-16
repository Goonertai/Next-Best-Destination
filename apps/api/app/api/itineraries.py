"""Endpoints for validating itinerary-generation inputs."""

from fastapi import APIRouter

from app.domain.schemas import PreferencesValidationResponse, TravelPreferences

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("/validate", response_model=PreferencesValidationResponse)
def validate_preferences(
    preferences: TravelPreferences,
) -> PreferencesValidationResponse:
    """Validate and normalize trip preferences without generating a plan."""
    return PreferencesValidationResponse(preferences=preferences)
