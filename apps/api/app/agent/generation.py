"""Itinerary-generation boundary and a safe deterministic demo implementation."""

from datetime import timedelta
from typing import Protocol

from app.domain.schemas import ItineraryDraft, ItineraryDraftDay, TravelPreferences


class ItineraryGenerator(Protocol):
    def generate(self, preferences: TravelPreferences) -> ItineraryDraft:
        """Create a draft from preferences."""


class DemoItineraryGenerator:
    """Return generic activity prompts without claiming real-world facts."""

    def generate(self, preferences: TravelPreferences) -> ItineraryDraft:
        # Treat the end date as the departure date, so it is not a planned day.
        day_count = (preferences.end_date - preferences.start_date).days
        days = [
            ItineraryDraftDay(
                date=preferences.start_date + timedelta(days=offset),
                suggestions=[
                    f"Consider a {interest.lower()}-focused activity in "
                    f"{preferences.destination}. Choose a specific venue only "
                    "after checking current listings."
                    for interest in preferences.interests
                ],
            )
            for offset in range(day_count)
        ]
        return ItineraryDraft(
            destination=preferences.destination,
            generation_mode="demo",
            is_complete_itinerary=False,
            uses_verified_place_data=False,
            notice=(
                "Template-based demo only: no specific venues, opening hours, "
                "prices, routes, or weather have been retrieved or verified."
            ),
            days=days,
        )
