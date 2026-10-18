"""Typed API and domain schemas for source-aware itineraries."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TravelPace(StrEnum):
    RELAXED = "relaxed"
    BALANCED = "balanced"
    PACKED = "packed"


class TravelPreferences(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    destination: Annotated[str, Field(min_length=1, max_length=160)]
    start_date: date
    end_date: date
    total_budget: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    travelers: Annotated[int, Field(ge=1, le=20)]
    interests: Annotated[list[str], Field(min_length=1, max_length=20)]
    preferences: Annotated[str, Field(max_length=2000)] = ""
    pace: TravelPace

    @field_validator("interests")
    @classmethod
    def interests_must_not_be_blank(cls, interests: list[str]) -> list[str]:
        cleaned = [interest.strip() for interest in interests]
        if any(not interest for interest in cleaned):
            raise ValueError("interests must not contain blank values")
        return cleaned

    @model_validator(mode="after")
    def dates_must_be_ordered(self) -> "TravelPreferences":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class PreferencesValidationResponse(BaseModel):
    status: str = "valid"
    preferences: TravelPreferences
    itinerary_generated: bool = False


class PlaceSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Annotated[str, Field(min_length=1, max_length=80)]
    url: Annotated[str, Field(min_length=1, max_length=2048)]
    retrieved_at: datetime


class PlaceReference(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=200)]
    place_id: Annotated[str, Field(min_length=1, max_length=256)]
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    source: PlaceSource


class Estimate(BaseModel):
    """An explicitly uncertain numeric estimate, never a verified quote."""

    amount: Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    is_estimate: bool

    @field_validator("is_estimate")
    @classmethod
    def must_be_labeled_estimate(cls, value: bool) -> bool:
        if not value:
            raise ValueError("cost amounts must be labeled as estimates")
        return value


class TravelTimeEstimate(BaseModel):
    minutes: Annotated[int, Field(gt=0, le=1440)]
    mode: Annotated[str, Field(min_length=1, max_length=40)]
    is_estimate: bool
    source: PlaceSource | None = None

    @model_validator(mode="after")
    def estimate_needs_source(self) -> "TravelTimeEstimate":
        if not self.is_estimate:
            raise ValueError("travel times must be labeled as estimates")
        if self.source is None:
            raise ValueError("travel-time estimates require source metadata")
        return self


class Activity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime
    end_time: datetime
    category: Annotated[str, Field(min_length=1, max_length=40)]
    place: PlaceReference
    description: Annotated[str, Field(min_length=1, max_length=1000)]
    estimated_cost: Estimate | None = None
    travel_from_previous: TravelTimeEstimate | None = None

    @model_validator(mode="after")
    def activity_times_must_be_ordered(self) -> "Activity":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ItineraryDay(BaseModel):
    date: date
    activities: list[Activity]


class Itinerary(BaseModel):
    id: str | None = None
    destination: Annotated[str, Field(min_length=1, max_length=160)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    days: list[ItineraryDay]
    total_estimated_cost: Estimate | None = None
    generated_at: datetime


class ItineraryDraftDay(BaseModel):
    """A date with non-factual activity prompts, not verified venues."""

    date: date
    suggestions: list[str]


class ItineraryDraft(BaseModel):
    """An explicitly incomplete demo draft with no verified travel data."""

    destination: Annotated[str, Field(min_length=1, max_length=160)]
    generation_mode: Literal["demo"]
    is_complete_itinerary: Literal[False]
    uses_verified_place_data: Literal[False]
    notice: str
    days: list[ItineraryDraftDay]
