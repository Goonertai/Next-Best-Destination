"""Safe natural-language edits for existing itinerary activities."""

import os
import re
from datetime import UTC, datetime, time
from typing import Literal

from agents import Agent, Runner, function_tool
from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas import Itinerary


class ItineraryEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    itinerary: Itinerary
    instruction: str = Field(min_length=3, max_length=1000)


class ItineraryEditCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["remove_activity", "move_activity", "unsupported"]
    place_id: str | None = None
    target_day: int | None = Field(default=None, ge=1, le=31)
    explanation: str = Field(min_length=1, max_length=300)


class ExistingActivity(BaseModel):
    place_id: str
    name: str
    day: int


class ExistingActivityList(BaseModel):
    activities: list[ExistingActivity]


class ItineraryEditResponse(BaseModel):
    itinerary: Itinerary
    edit_mode: Literal["agents_sdk", "safe_rule"]
    summary: str


def apply_natural_language_edit(itinerary: Itinerary, instruction: str) -> ItineraryEditResponse:
    if os.environ.get("OPENAI_API_KEY", "").strip():
        command = _command_with_agent(itinerary, instruction)
        mode: Literal["agents_sdk", "safe_rule"] = "agents_sdk"
    else:
        command = _command_with_rules(itinerary, instruction)
        mode = "safe_rule"
    updated, summary = apply_edit_command(itinerary, command)
    return ItineraryEditResponse(itinerary=updated, edit_mode=mode, summary=summary)


def _command_with_agent(itinerary: Itinerary, instruction: str) -> ItineraryEditCommand:
    activities = ExistingActivityList(
        activities=[
            ExistingActivity(
                place_id=activity.place.place_id,
                name=activity.place.name,
                day=day_index,
            )
            for day_index, day in enumerate(itinerary.days, start=1)
            for activity in day.activities
        ]
    )

    @function_tool(
        name_override="list_existing_activities",
        description_override=(
            "List the only existing activities that can be edited. Use these exact place IDs; "
            "do not invent a place or ID."
        ),
        output_type=ExistingActivityList,
    )
    async def list_existing_activities() -> ExistingActivityList:
        return activities

    agent = Agent(
        name="Itinerary Editor",
        instructions=(
            "Convert the user's request into one safe edit command. Call "
            "list_existing_activities before deciding. You may only remove or move an activity "
            "whose exact place_id is in that tool result. Do not add activities, prices, hours, "
            "availability, travel estimates, or weather. For requests outside remove/move, return "
            "action unsupported and explain what is supported. Day numbers are 1-based."
        ),
        tools=[list_existing_activities],
        output_type=ItineraryEditCommand,
    )
    result = Runner.run_sync(agent, input=instruction)
    if not isinstance(result.final_output, ItineraryEditCommand):
        raise ValueError("The itinerary editor did not return a valid edit command.")
    return result.final_output


def _command_with_rules(itinerary: Itinerary, instruction: str) -> ItineraryEditCommand:
    remove_match = re.search(r"\b(?:remove|delete|drop|skip)\s+(.+?)\s*[.!?]*$", instruction, re.I)
    move_match = re.search(
        r"\b(?:move|relocate)\s+(.+?)\s+to\s+day\s+(\d+)\b",
        instruction,
        re.I,
    )
    if remove_match:
        place_id = _match_place(itinerary, remove_match.group(1))
        if place_id:
            return ItineraryEditCommand(
                action="remove_activity",
                place_id=place_id,
                explanation="Removed the named activity.",
            )
    if move_match:
        place_id = _match_place(itinerary, move_match.group(1))
        if place_id:
            return ItineraryEditCommand(
                action="move_activity",
                place_id=place_id,
                target_day=int(move_match.group(2)),
                explanation=f"Moved the named activity to day {move_match.group(2)}.",
            )
    return ItineraryEditCommand(
        action="unsupported",
        explanation=(
            "With no OPENAI_API_KEY, sample mode only supports sample edits like "
            "'remove Sample attraction 1' or 'move Sample attraction 1 to day 2'."
        ),
    )


def _match_place(itinerary: Itinerary, target: str) -> str | None:
    normalized_target = _normalize(target)
    if not normalized_target:
        return None
    matches = {
        activity.place.place_id
        for day in itinerary.days
        for activity in day.activities
        if normalized_target in _normalize(activity.place.name)
        or normalized_target == _normalize(activity.place.place_id)
    }
    return next(iter(matches)) if len(matches) == 1 else None


def _normalize(value: str) -> str:
    return " ".join(
        "".join(character if character.isalnum() else " " for character in value.casefold()).split()
    )


def apply_edit_command(
    itinerary: Itinerary, command: ItineraryEditCommand
) -> tuple[Itinerary, str]:
    if command.action == "unsupported":
        raise ValueError(command.explanation)
    if command.place_id is None:
        raise ValueError("The requested activity could not be identified.")

    locations = [
        (day_index, activity_index)
        for day_index, day in enumerate(itinerary.days)
        for activity_index, activity in enumerate(day.activities)
        if activity.place.place_id == command.place_id
    ]
    if len(locations) != 1:
        raise ValueError("The activity ID does not identify exactly one itinerary item.")
    source_day, activity_index = locations[0]
    days = list(itinerary.days)
    source = days[source_day]
    activity = source.activities[activity_index]

    if command.action == "remove_activity":
        updated_activities = [
            item for index, item in enumerate(source.activities) if index != activity_index
        ]
        days[source_day] = _invalidate_day_data(source, updated_activities)
        summary = f"Removed {activity.place.name} from day {source_day + 1}."
    else:
        target_day = (command.target_day or 0) - 1
        if target_day < 0 or target_day >= len(days):
            raise ValueError("Choose a day number within this itinerary.")
        if target_day == source_day:
            raise ValueError("That activity is already on the requested day.")
        source_activities = [
            item for index, item in enumerate(source.activities) if index != activity_index
        ]
        target = days[target_day]
        moved = _reschedule_activity(activity, target)
        days[source_day] = _invalidate_day_data(source, source_activities)
        days[target_day] = _invalidate_day_data(target, [*target.activities, moved])
        summary = f"Moved {activity.place.name} from day {source_day + 1} to day {target_day + 1}."

    warnings = [warning for warning in itinerary.warnings if not warning.startswith("Edited day ")]
    affected_days = {source_day}
    if command.action == "move_activity" and command.target_day is not None:
        affected_days.add(command.target_day - 1)
    warnings.extend(
        f"Edited day {day_index + 1}: weather and route estimates were cleared "
        "because the plan changed."
        for day_index in sorted(affected_days)
    )
    updated = itinerary.model_copy(
        update={
            "id": None,
            "days": days,
            "warnings": list(dict.fromkeys(warnings)),
            "generated_at": datetime.now(UTC),
        }
    )
    return updated, summary


def _invalidate_day_data(day, activities):
    reset_activities = [
        activity.model_copy(update={"travel_from_previous": None}) for activity in activities
    ]
    return day.model_copy(
        update={
            "activities": reset_activities,
            "weather": None,
            "area_id": None,
        }
    )


def _reschedule_activity(activity, target_day):
    existing_slots = {item.start_time.hour for item in target_day.activities}
    hour = next(
        (candidate for candidate in (9, 12, 15, 18) if candidate not in existing_slots),
        None,
    )
    if hour is None:
        raise ValueError("The target day already has four activities; remove one first.")
    date_value = target_day.date
    return activity.model_copy(
        update={
            "start_time": datetime.combine(date_value, time(hour=hour)),
            "end_time": datetime.combine(date_value, time(hour=hour + 1)),
            "travel_from_previous": None,
        }
    )
