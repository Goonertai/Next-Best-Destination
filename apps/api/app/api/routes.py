"""HTTP endpoint for sourced route-duration estimates."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.schemas import RouteEstimate, RouteEstimateRequest
from app.providers.errors import (
    ProviderNotConfiguredError,
    ProviderRequestError,
    RouteNotFoundError,
)
from app.providers.factory import get_routes_provider as create_routes_provider
from app.providers.routes import RoutesProvider

router = APIRouter(prefix="/routes", tags=["routes"])


def get_routes_provider() -> RoutesProvider:
    try:
        return create_routes_provider()
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/estimate", response_model=RouteEstimate)
def estimate_route(
    request: RouteEstimateRequest,
    provider: Annotated[RoutesProvider, Depends(get_routes_provider)],
) -> RouteEstimate:
    try:
        return provider.compute_route(request)
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Routes API request failed. Try again later.",
        ) from exc
