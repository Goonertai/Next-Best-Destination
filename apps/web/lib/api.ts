import type { TravelPreferencesInput } from "./preferences";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ItineraryDraft = {
  destination: string;
  generation_mode: "demo";
  is_complete_itinerary: false;
  uses_verified_place_data: false;
  notice: string;
  days: Array<{
    date: string;
    suggestions: string[];
  }>;
};

export type GenerateItineraryRequest = {
  destination: string;
  start_date: string;
  end_date: string;
  total_budget: string;
  currency: string;
  travelers: number;
  interests: string[];
  preferences: string;
  pace: string;
};

export async function getApiHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!response.ok)
    throw new Error(`API health check failed: ${response.status}`);
  return response.json() as Promise<{ status: string }>;
}

export async function generateDemoItinerary(
  values: TravelPreferencesInput,
): Promise<ItineraryDraft> {
  const request: GenerateItineraryRequest = {
    destination: values.destination.trim(),
    start_date: values.startDate,
    end_date: values.endDate,
    total_budget: values.totalBudget,
    currency: values.currency,
    travelers: Number(values.travelers),
    interests: values.interests,
    preferences: values.preferences,
    pace: values.pace,
  };

  const response = await fetch(`${API_BASE_URL}/itineraries/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `Itinerary request failed: ${response.status}. Check the API and trip details, then try again.`,
    );
  }

  return response.json() as Promise<ItineraryDraft>;
}
