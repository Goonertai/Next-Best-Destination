"""Factories for live Google Maps providers."""

import os

from app.providers.errors import ProviderNotConfiguredError
from app.providers.places import GooglePlacesProvider
from app.providers.routes import GoogleRoutesProvider


def _google_maps_api_key() -> str:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        raise ProviderNotConfiguredError(
            "Google Maps data is unavailable until GOOGLE_MAPS_API_KEY is configured."
        )
    return api_key


def get_places_provider() -> GooglePlacesProvider:
    return GooglePlacesProvider(_google_maps_api_key())


def get_routes_provider() -> GoogleRoutesProvider:
    return GoogleRoutesProvider(_google_maps_api_key())
