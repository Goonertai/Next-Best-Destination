"""HTTP endpoints for sourced place discovery and identifier validation."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domain.schemas import (
    PlaceCategory,
    PlaceSearchResponse,
    PlaceValidationRequest,
    PlaceValidationResponse,
)
from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError
from app.providers.factory import get_places_provider as create_places_provider
from app.providers.places import PlacesProvider
from app.services.places import search_places, validate_place_reference

router = APIRouter(prefix="/places", tags=["places"])


def get_places_provider() -> PlacesProvider:
    try:
        return create_places_provider()
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def _search(
    category: PlaceCategory,
    destination: str,
    limit: int,
    provider: PlacesProvider,
) -> PlaceSearchResponse:
    try:
        return search_places(
            provider,
            destination=destination.strip(),
            category=category,
            limit=limit,
        )
    except ProviderRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places API request failed. Try again later.",
        ) from exc


@router.get("/attractions", response_model=PlaceSearchResponse)
def discover_attractions(
    destination: Annotated[str, Query(min_length=1, max_length=160)],
    provider: Annotated[PlacesProvider, Depends(get_places_provider)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> PlaceSearchResponse:
    return _search("attractions", destination, limit, provider)


@router.get("/restaurants", response_model=PlaceSearchResponse)
def discover_restaurants(
    destination: Annotated[str, Query(min_length=1, max_length=160)],
    provider: Annotated[PlacesProvider, Depends(get_places_provider)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> PlaceSearchResponse:
    return _search("restaurants", destination, limit, provider)


@router.post("/validate", response_model=PlaceValidationResponse)
def validate_place(
    request: PlaceValidationRequest,
    provider: Annotated[PlacesProvider, Depends(get_places_provider)],
) -> PlaceValidationResponse:
    try:
        return validate_place_reference(provider, request)
    except ProviderRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places API request failed. Try again later.",
        ) from exc
