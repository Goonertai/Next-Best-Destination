import type { TravelPreferencesInput } from "./preferences";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Itinerary = {
  id: string | null;
  destination: string;
  currency: string;
  generation_mode: "demo" | "live";
  data_status: "live" | "mock" | "unavailable";
  notice: string;
  warnings: string[];
  total_estimated_cost: {
    amount: string;
    currency: string;
    is_estimate: true;
  } | null;
  generated_at: string;
  days: Array<{
    date: string;
    area_id: string | null;
    weather: {
      forecast_date: string;
      timezone: string;
      weather_code: number;
      temperature_max_c: number;
      temperature_min_c: number;
      precipitation_probability_max_pct: number | null;
      data_status: "live" | "mock" | "unavailable";
      source: { provider: string; url: string; retrieved_at: string };
    } | null;
    activities: Array<{
      start_time: string;
      end_time: string;
      category: string;
      description: string;
      place_is_verified: boolean;
      data_status: "live" | "mock" | "unavailable";
      place: {
        name: string;
        place_id: string;
        latitude: number;
        longitude: number;
        source: { provider: string; url: string; retrieved_at: string };
      };
      travel_from_previous: {
        minutes: number;
        mode: string;
        is_estimate: true;
        source: { provider: string; url: string; retrieved_at: string };
      } | null;
      estimated_cost: {
        amount: string;
        currency: string;
        is_estimate: true;
      } | null;
    }>;
  }>;
};

export type ItineraryEditResponse = {
  itinerary: Itinerary;
  edit_mode: "agents_sdk" | "safe_rule";
  summary: string;
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
  data_mode: "demo" | "live";
};

export async function getApiHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!response.ok)
    throw new Error(`API health check failed: ${response.status}`);
  return response.json() as Promise<{ status: string }>;
}

export async function generateItinerary(
  values: TravelPreferencesInput,
  dataMode: "demo" | "live",
): Promise<Itinerary> {
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
    data_mode: dataMode,
  };

  const response = await fetch(`${API_BASE_URL}/itineraries/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    cache: "no-store",
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      body?.detail ??
        `Itinerary request failed: ${response.status}. Check the API and trip details, then try again.`,
    );
  }

  return response.json() as Promise<Itinerary>;
}

export async function saveItinerary(itinerary: Itinerary): Promise<Itinerary> {
  const response = await fetch(`${API_BASE_URL}/itineraries/saved`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(itinerary),
    cache: "no-store",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      body?.detail ?? `Could not save itinerary: ${response.status}`,
    );
  }
  return response.json() as Promise<Itinerary>;
}

export async function listSavedItineraries(): Promise<Itinerary[]> {
  const response = await fetch(`${API_BASE_URL}/itineraries/saved`, {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(`Could not load saved trips: ${response.status}`);
  return response.json() as Promise<Itinerary[]>;
}

export async function getSavedItinerary(id: string): Promise<Itinerary> {
  const response = await fetch(
    `${API_BASE_URL}/itineraries/${encodeURIComponent(id)}`,
    { cache: "no-store" },
  );
  if (!response.ok)
    throw new Error(`Could not open saved itinerary: ${response.status}`);
  return response.json() as Promise<Itinerary>;
}

export async function editItinerary(
  itinerary: Itinerary,
  instruction: string,
): Promise<ItineraryEditResponse> {
  const response = await fetch(`${API_BASE_URL}/itineraries/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ itinerary, instruction }),
    cache: "no-store",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      body?.detail ?? `Could not update itinerary: ${response.status}`,
    );
  }
  return response.json() as Promise<ItineraryEditResponse>;
}
