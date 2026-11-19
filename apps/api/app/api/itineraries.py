"""Endpoints for validating itinerary-generation inputs."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.agent.generation import DemoItineraryGenerator, ItineraryGenerator
from app.agent.itinerary_edits import (
    ItineraryEditRequest,
    ItineraryEditResponse,
    apply_natural_language_edit,
)
from app.agent.tools import (
    ActivityIdeasRequest,
    ActivityIdeasResult,
    suggest_activity_ideas,
)
from app.domain.schemas import (
    Itinerary,
    ItineraryDraft,
    ItineraryPlanRequest,
    PreferencesValidationResponse,
    TravelPreferences,
)
from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError
from app.repositories.itineraries import ItineraryRepository, SqlAlchemyItineraryRepository
from app.services.itinerary_planning import ItineraryPlanner

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


def get_itinerary_generator() -> ItineraryGenerator:
    """Provide the no-credential demo implementation until LLM setup is available."""
    return DemoItineraryGenerator()


def get_itinerary_planner() -> ItineraryPlanner:
    """Create the full planner; provider credentials are resolved per request."""
    return ItineraryPlanner()


@lru_cache(maxsize=1)
def get_itinerary_repository() -> ItineraryRepository:
    """Use a local SQLite file by default or DATABASE_URL when configured."""
    return SqlAlchemyItineraryRepository()


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


@router.post("/plan", response_model=Itinerary)
def generate_itinerary(
    request: ItineraryPlanRequest,
    planner: Annotated[ItineraryPlanner, Depends(get_itinerary_planner)],
) -> Itinerary:
    """Generate a complete sample plan or a source-backed live plan."""
    try:
        return planner.plan(request)
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ProviderRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="A required travel-data provider failed. No unverified venues were added.",
        ) from exc


@router.post("/saved", response_model=Itinerary, status_code=status.HTTP_201_CREATED)
def save_itinerary(
    itinerary: Itinerary,
    repository: Annotated[ItineraryRepository, Depends(get_itinerary_repository)],
) -> Itinerary:
    try:
        return repository.save(itinerary)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Itinerary storage is unavailable. Check DATABASE_URL and try again.",
        ) from exc


@router.get("/saved", response_model=list[Itinerary])
def list_saved_itineraries(
    repository: Annotated[ItineraryRepository, Depends(get_itinerary_repository)],
    limit: int = Query(default=20, ge=1, le=50),
) -> list[Itinerary]:
    try:
        return repository.list_recent(limit)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Itinerary storage is unavailable. Check DATABASE_URL and try again.",
        ) from exc


@router.get("/{itinerary_id}", response_model=Itinerary)
def get_saved_itinerary(
    itinerary_id: str,
    repository: Annotated[ItineraryRepository, Depends(get_itinerary_repository)],
) -> Itinerary:
    try:
        itinerary = repository.get(itinerary_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Itinerary storage is unavailable. Check DATABASE_URL and try again.",
        ) from exc
    if itinerary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved itinerary was found with that ID.",
        )
    return itinerary


@router.post("/edit", response_model=ItineraryEditResponse)
def edit_itinerary(request: ItineraryEditRequest) -> ItineraryEditResponse:
    """Apply a constrained natural-language edit to existing itinerary activities."""
    try:
        result = apply_natural_language_edit(request.itinerary, request.instruction)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "The AI itinerary editor is unavailable. Try again or use a supported sample edit."
            ),
        ) from exc

    return result


@router.post("/activity-ideas", response_model=ActivityIdeasResult)
def generate_activity_ideas(request: ActivityIdeasRequest) -> ActivityIdeasResult:
    """Return deterministic generic prompts; this does not search real-world listings."""
    return suggest_activity_ideas(request)
