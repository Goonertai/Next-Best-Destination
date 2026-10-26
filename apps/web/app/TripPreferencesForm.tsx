"use client";

import { useState, type FormEvent } from "react";
import { generateDemoItinerary, type ItineraryDraft } from "../lib/api";
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
  const [errors, setErrors] = useState<TravelPreferencesErrors>({});
  const [itinerary, setItinerary] = useState<ItineraryDraft | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  function updateValue<Key extends keyof TravelPreferencesInput>(
    key: Key,
    value: TravelPreferencesInput[Key],
  ) {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
    setItinerary(null);
    setRequestError(null);
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
      setItinerary(await generateDemoItinerary(values));
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
          {isGenerating ? "Putting ideas together…" : "Generate a first draft"}
          {!isGenerating && <span aria-hidden="true">→</span>}
        </button>
        {isGenerating && (
          <p className="form-success" role="status">
            Preparing generic ideas for your trip…
          </p>
        )}
        {requestError && (
          <p className="form-error" role="alert">
            {requestError}
          </p>
        )}
      </div>
      {itinerary && <ItineraryDisplay itinerary={itinerary} />}
    </form>
  );
}
