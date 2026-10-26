import { afterEach, describe, expect, it, vi } from "vitest";
import { generateDemoItinerary, getApiHealth } from "./api";

describe("getApiHealth", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns the API health payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) }),
    );

    await expect(getApiHealth()).resolves.toEqual({ status: "ok" });
  });

  it("surfaces non-success API responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503 }),
    );

    await expect(getApiHealth()).rejects.toThrow(
      "API health check failed: 503",
    );
  });
});

describe("generateDemoItinerary", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("posts validated trip preferences and returns the dated draft", async () => {
    const draft = {
      destination: "Montreal",
      generation_mode: "demo" as const,
      is_complete_itinerary: false as const,
      uses_verified_place_data: false as const,
      notice: "No places have been checked.",
      days: [{ date: "2026-11-07", suggestions: ["Explore local history."] }],
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => draft,
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      generateDemoItinerary({
        destination: "Montreal",
        startDate: "2026-11-07",
        endDate: "2026-11-08",
        totalBudget: "1500",
        currency: "CAD",
        travelers: "2",
        interests: ["History"],
        preferences: "",
        pace: "relaxed",
      }),
    ).resolves.toEqual(draft);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/itineraries/generate",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destination: "Montreal",
          start_date: "2026-11-07",
          end_date: "2026-11-08",
          total_budget: "1500",
          currency: "CAD",
          travelers: 2,
          interests: ["History"],
          preferences: "",
          pace: "relaxed",
        }),
        cache: "no-store",
      }),
    );
  });

  it("returns a useful error when the API rejects the request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 422 }),
    );

    await expect(
      generateDemoItinerary({
        destination: "Montreal",
        startDate: "2026-11-07",
        endDate: "2026-11-08",
        totalBudget: "1500",
        currency: "CAD",
        travelers: "2",
        interests: ["History"],
        preferences: "",
        pace: "relaxed",
      }),
    ).rejects.toThrow("Itinerary request failed: 422");
  });
});
