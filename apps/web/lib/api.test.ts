import { afterEach, describe, expect, it, vi } from "vitest";
import { generateItinerary, getApiHealth } from "./api";

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

describe("generateItinerary", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("posts trip preferences and the selected data mode", async () => {
    const itinerary = {
      id: null,
      destination: "Montreal",
      currency: "CAD",
      generation_mode: "demo" as const,
      data_status: "mock" as const,
      notice: "Sample data only.",
      warnings: [],
      total_estimated_cost: null,
      generated_at: "2026-11-07T12:00:00Z",
      days: [],
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => itinerary,
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      generateItinerary(
        {
          destination: "Montreal",
          startDate: "2026-11-07",
          endDate: "2026-11-08",
          totalBudget: "1500",
          currency: "CAD",
          travelers: "2",
          interests: ["History"],
          preferences: "",
          pace: "relaxed",
        },
        "demo",
      ),
    ).resolves.toEqual(itinerary);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/itineraries/plan",
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
          data_mode: "demo",
        }),
        cache: "no-store",
      }),
    );
  });

  it("returns a useful error when the API rejects the request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({}),
      }),
    );

    await expect(
      generateItinerary(
        {
          destination: "Montreal",
          startDate: "2026-11-07",
          endDate: "2026-11-08",
          totalBudget: "1500",
          currency: "CAD",
          travelers: "2",
          interests: ["History"],
          preferences: "",
          pace: "relaxed",
        },
        "live",
      ),
    ).rejects.toThrow("Itinerary request failed: 422");
  });

  it("shows the provider setup detail for unavailable live mode", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ detail: "Configure GOOGLE_MAPS_API_KEY." }),
      }),
    );

    await expect(
      generateItinerary(
        {
          destination: "Montreal",
          startDate: "2026-11-07",
          endDate: "2026-11-08",
          totalBudget: "1500",
          currency: "CAD",
          travelers: "2",
          interests: ["History"],
          preferences: "",
          pace: "relaxed",
        },
        "live",
      ),
    ).rejects.toThrow("Configure GOOGLE_MAPS_API_KEY.");
  });
});
