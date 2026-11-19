"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  editItinerary,
  generateItinerary,
  getSavedItinerary,
  listSavedItineraries,
  saveItinerary,
  type Itinerary,
} from "../lib/api";
import {
  TRAVEL_INTERESTS,
  TRAVEL_PACES,
  validateTravelPreferences,
  type TravelPace,
  type TravelPreferencesErrors,
  type TravelPreferencesInput,
} from "../lib/preferences";
import { ItineraryDisplay } from "./ItineraryDisplay";

const initialValues: TravelPreferencesInput = {
  destination: "",
  startDate: "",
  endDate: "",
  totalBudget: "",
  currency: "CAD",
  travelers: "2",
  interests: [],
  preferences: "",
  pace: "balanced",
};

const paceLabels: Record<TravelPace, string> = {
  relaxed: "Relaxed",
  balanced: "Balanced",
  packed: "Full days",
};

export function TripPreferencesForm() {
  const [values, setValues] = useState(initialValues);
  const [dataMode, setDataMode] = useState<"demo" | "live">("demo");
  const [errors, setErrors] = useState<TravelPreferencesErrors>({});
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedItineraries, setSavedItineraries] = useState<Itinerary[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [shareNotice, setShareNotice] = useState<string | null>(null);
  const [editInstruction, setEditInstruction] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    let active = true;
    const sharedId = new URLSearchParams(window.location.search).get(
      "itinerary",
    );
    if (sharedId) {
      getSavedItinerary(sharedId)
        .then((saved) => {
          if (active) {
            setItinerary(saved);
            setSaveNotice("Shared itinerary opened.");
          }
        })
        .catch((error: unknown) => {
          if (active) {
            setRequestError(
              error instanceof Error
                ? error.message
                : "Could not open shared itinerary.",
            );
          }
        });
    }
    listSavedItineraries()
      .then((saved) => {
        if (active) setSavedItineraries(saved);
      })
      .catch((error: unknown) => {
        if (active) {
          setRequestError(
            error instanceof Error
              ? error.message
              : "Saved trips are unavailable.",
          );
        }
      })
      .finally(() => {
        if (active) setHistoryLoaded(true);
      });
    return () => {
      active = false;
    };
  }, []);

  function updateValue<Key extends keyof TravelPreferencesInput>(
    key: Key,
    value: TravelPreferencesInput[Key],
  ) {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
    setItinerary(null);
    setRequestError(null);
    setSaveNotice(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validateTravelPreferences(values);
    setErrors(nextErrors);
    setItinerary(null);
    setRequestError(null);

    if (Object.keys(nextErrors).length > 0) return;

    setIsGenerating(true);
    try {
      setItinerary(await generateItinerary(values, dataMode));
      setSaveNotice(null);
    } catch (error) {
      setRequestError(
        error instanceof Error
          ? error.message
          : "Could not generate the demo itinerary. Please try again.",
      );
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleSaveItinerary() {
    if (!itinerary) return;
    setIsSaving(true);
    setRequestError(null);
    try {
      const saved = await saveItinerary(itinerary);
      setItinerary(saved);
      setSavedItineraries((current) => [
        saved,
        ...current.filter((item) => item.id !== saved.id),
      ]);
      setSaveNotice("Itinerary saved. You can reopen it from Saved trips.");
      setShareNotice(null);
    } catch (error) {
      setRequestError(
        error instanceof Error ? error.message : "Could not save itinerary.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCopyShareLink() {
    if (!itinerary?.id) return;
    const shareUrl = new URL(window.location.href);
    shareUrl.search = new URLSearchParams({
      itinerary: itinerary.id,
    }).toString();
    try {
      await navigator.clipboard.writeText(shareUrl.toString());
      setShareNotice(
        "Share link copied. Anyone with this link can view this saved snapshot.",
      );
    } catch {
      setShareNotice(shareUrl.toString());
    }
  }

  async function handleOpenSaved(id: string) {
    setRequestError(null);
    try {
      setItinerary(await getSavedItinerary(id));
      setSaveNotice("Saved itinerary opened.");
    } catch (error) {
      setRequestError(
        error instanceof Error
          ? error.message
          : "Could not open saved itinerary.",
      );
    }
  }

  async function handleEditItinerary() {
    if (!itinerary || !editInstruction.trim()) return;
    setIsEditing(true);
    setRequestError(null);
    try {
      const result = await editItinerary(itinerary, editInstruction);
      setItinerary(result.itinerary);
      setEditInstruction("");
      setSaveNotice(
        `${result.summary} ${result.edit_mode === "agents_sdk" ? "Updated with the AI editor." : "Applied with the sample command editor."}`,
      );
    } catch (error) {
      setRequestError(
        error instanceof Error ? error.message : "Could not edit itinerary.",
      );
    } finally {
      setIsEditing(false);
    }
  }

  return (
    <form className="preferences-form" onSubmit={handleSubmit} noValidate>
      <div className="form-grid">
        <div className="form-field form-field-wide">
          <label htmlFor="destination">Where are you going?</label>
          <input
            autoComplete="off"
            id="destination"
            name="destination"
            placeholder="City or region"
            value={values.destination}
            onChange={(event) => updateValue("destination", event.target.value)}
            aria-invalid={Boolean(errors.destination)}
            aria-describedby={
              errors.destination ? "destination-error" : undefined
            }
          />
          {errors.destination && (
            <p className="form-error" id="destination-error">
              {errors.destination}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="start-date">Start date</label>
          <input
            id="start-date"
            name="startDate"
            type="date"
            value={values.startDate}
            onChange={(event) => updateValue("startDate", event.target.value)}
            aria-invalid={Boolean(errors.startDate)}
            aria-describedby={errors.startDate ? "start-date-error" : undefined}
          />
          {errors.startDate && (
            <p className="form-error" id="start-date-error">
              {errors.startDate}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="end-date">End date</label>
          <input
            id="end-date"
            name="endDate"
            type="date"
            value={values.endDate}
            onChange={(event) => updateValue("endDate", event.target.value)}
            aria-invalid={Boolean(errors.endDate)}
            aria-describedby={errors.endDate ? "end-date-error" : undefined}
          />
          {errors.endDate && (
            <p className="form-error" id="end-date-error">
              {errors.endDate}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="total-budget">Total trip budget</label>
          <input
            id="total-budget"
            name="totalBudget"
            type="number"
            min="0.01"
            step="0.01"
            inputMode="decimal"
            placeholder="2500"
            value={values.totalBudget}
            onChange={(event) => updateValue("totalBudget", event.target.value)}
            aria-invalid={Boolean(errors.totalBudget)}
            aria-describedby={
              errors.totalBudget ? "budget-error" : "budget-help"
            }
          />
          <p className="form-hint" id="budget-help">
            Enter the total budget for everyone traveling.
          </p>
          {errors.totalBudget && (
            <p className="form-error" id="budget-error">
              {errors.totalBudget}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="currency">Currency</label>
          <select
            id="currency"
            name="currency"
            value={values.currency}
            onChange={(event) => updateValue("currency", event.target.value)}
            aria-invalid={Boolean(errors.currency)}
            aria-describedby={errors.currency ? "currency-error" : undefined}
          >
            <option value="CAD">CAD — Canadian dollar</option>
            <option value="USD">USD — US dollar</option>
            <option value="EUR">EUR — Euro</option>
            <option value="GBP">GBP — Pound sterling</option>
            <option value="AUD">AUD — Australian dollar</option>
            <option value="JPY">JPY — Japanese yen</option>
          </select>
          {errors.currency && (
            <p className="form-error" id="currency-error">
              {errors.currency}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="travelers">Number of travelers</label>
          <input
            id="travelers"
            name="travelers"
            type="number"
            min="1"
            max="20"
            step="1"
            value={values.travelers}
            onChange={(event) => updateValue("travelers", event.target.value)}
            aria-invalid={Boolean(errors.travelers)}
            aria-describedby={errors.travelers ? "travelers-error" : undefined}
          />
          {errors.travelers && (
            <p className="form-error" id="travelers-error">
              {errors.travelers}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="data-mode">Planning data</label>
          <select
            id="data-mode"
            value={dataMode}
            onChange={(event) => {
              setDataMode(event.target.value as "demo" | "live");
              setItinerary(null);
              setRequestError(null);
            }}
          >
            <option value="demo">Sample demo data (fictional)</option>
            <option value="live">Live Google places</option>
          </select>
          <p className="form-hint">
            Live mode requires a server-side Google Maps API key. Sample data is
            synthetic and not for travel decisions.
          </p>
        </div>
      </div>

      <fieldset className="form-fieldset">
        <legend>What are you interested in?</legend>
        <div className="interest-options">
          {TRAVEL_INTERESTS.map((interest) => (
            <label className="interest-option" key={interest}>
              <input
                type="checkbox"
                name="interests"
                value={interest}
                checked={values.interests.includes(interest)}
                onChange={(event) => {
                  const interests = event.target.checked
                    ? [...values.interests, interest]
                    : values.interests.filter((item) => item !== interest);
                  updateValue("interests", interests);
                }}
                aria-invalid={Boolean(errors.interests)}
                aria-describedby={
                  errors.interests ? "interests-error" : undefined
                }
              />
              {interest}
            </label>
          ))}
        </div>
        {errors.interests && (
          <p className="form-error" id="interests-error">
            {errors.interests}
          </p>
        )}
      </fieldset>

      <fieldset className="form-fieldset">
        <legend>What pace feels right?</legend>
        <div className="pace-options">
          {TRAVEL_PACES.map((pace) => (
            <label className="pace-option" key={pace}>
              <input
                type="radio"
                name="pace"
                value={pace}
                checked={values.pace === pace}
                onChange={(event) => updateValue("pace", event.target.value)}
                aria-describedby={errors.pace ? "pace-error" : undefined}
              />
              <span>{paceLabels[pace]}</span>
            </label>
          ))}
        </div>
        {errors.pace && (
          <p className="form-error" id="pace-error">
            {errors.pace}
          </p>
        )}
      </fieldset>

      <div className="form-field">
        <label htmlFor="preferences">Any preferences or must-haves?</label>
        <textarea
          id="preferences"
          name="preferences"
          placeholder="For example: vegetarian-friendly restaurants, step-free routes"
          rows={3}
          value={values.preferences}
          onChange={(event) => updateValue("preferences", event.target.value)}
        />
      </div>

      <div className="form-submit-row">
        <button
          className="primary-button"
          type="submit"
          disabled={isGenerating}
        >
          {isGenerating ? "Planning your days…" : "Generate itinerary"}
          {!isGenerating && <span aria-hidden="true">→</span>}
        </button>
        {isGenerating && (
          <p className="form-success" role="status">
            Searching places and organizing your days…
          </p>
        )}
        {requestError && (
          <p className="form-error" role="alert">
            {requestError}
          </p>
        )}
      </div>
      {itinerary && (
        <div className="itinerary-result">
          <ItineraryDisplay itinerary={itinerary} />
          <div className="itinerary-edit">
            <label htmlFor="edit-instruction">Ask to change this plan</label>
            <textarea
              id="edit-instruction"
              value={editInstruction}
              onChange={(event) => setEditInstruction(event.target.value)}
              placeholder="For example: move Sample attraction 1 (fictional) to day 2"
              rows={2}
            />
            <p>
              With OPENAI_API_KEY, the Agents SDK can interpret requests.
              Without it, sample mode supports removing or moving an existing
              activity.
            </p>
            <button
              className="secondary-button"
              type="button"
              onClick={handleEditItinerary}
              disabled={isEditing || !editInstruction.trim()}
            >
              {isEditing ? "Updating plan…" : "Apply edit"}
            </button>
          </div>
          <div className="itinerary-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={handleSaveItinerary}
              disabled={isSaving}
            >
              {isSaving
                ? "Saving…"
                : itinerary.id
                  ? "Save new version"
                  : "Save itinerary"}
            </button>
            <button
              className="text-button"
              type="button"
              disabled={!itinerary.id}
              onClick={handleCopyShareLink}
            >
              Copy share link
            </button>
            {saveNotice && <p role="status">{saveNotice}</p>}
            {shareNotice && <p role="status">{shareNotice}</p>}
          </div>
        </div>
      )}
      <section className="saved-trips" aria-labelledby="saved-trips-title">
        <div>
          <p className="eyebrow">YOUR LIBRARY</p>
          <h3 id="saved-trips-title">Saved trips</h3>
        </div>
        {!historyLoaded ? (
          <p className="form-hint">Loading saved trips…</p>
        ) : savedItineraries.length === 0 ? (
          <p className="form-hint">
            No saved trips yet. Save a generated itinerary to find it here.
          </p>
        ) : (
          <ul>
            {savedItineraries.map((saved) => (
              <li key={saved.id}>
                <div>
                  <strong>{saved.destination}</strong>
                  <span>
                    {saved.days[0]?.date ?? "No dates"} ·{" "}
                    {saved.generation_mode === "demo"
                      ? "sample data"
                      : "live data"}
                  </span>
                </div>
                <button
                  className="text-button"
                  type="button"
                  onClick={() => saved.id && handleOpenSaved(saved.id)}
                >
                  Open
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </form>
  );
}
