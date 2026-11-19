import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Itinerary } from "../lib/api";
import { ItineraryDisplay } from "./ItineraryDisplay";

const source = {
  provider: "Synthetic demo fixture (not real travel data)",
  url: "https://example.test/demo/place",
  retrieved_at: "2026-11-07T12:00:00Z",
};

function sampleItinerary(days: Itinerary["days"]): Itinerary {
  return {
    id: null,
    destination: "Montreal",
    currency: "CAD",
    generation_mode: "demo",
    data_status: "mock",
    notice: "Sample data only; no real venues are shown.",
    warnings: [],
    total_estimated_cost: null,
    generated_at: "2026-11-07T12:00:00Z",
    days,
  };
}

const activity: Itinerary["days"][number]["activities"][number] = {
  start_time: "2026-11-07T09:00:00",
  end_time: "2026-11-07T10:00:00",
  category: "attraction",
  description: "Retrieved from a category search.",
  place_is_verified: false,
  data_status: "mock",
  place: {
    name: "Sample attraction 1 (fictional)",
    place_id: "demo-1",
    latitude: 1,
    longitude: 2,
    source,
  },
  travel_from_previous: null,
  estimated_cost: null,
};

describe("ItineraryDisplay", () => {
  it("shows dates, synthetic place labels, source links, and price uncertainty", () => {
    const markup = renderToStaticMarkup(
      createElement(ItineraryDisplay, {
        itinerary: sampleItinerary([
          {
            date: "2026-11-07",
            area_id: "area-1",
            weather: null,
            activities: [activity],
          },
          { date: "2026-11-08", area_id: null, weather: null, activities: [] },
        ]),
      }),
    );

    expect(markup).toContain("Your trip to Montreal.");
    expect(markup).toContain("Sample data · fictional");
    expect(markup).toContain("Saturday, November 7");
    expect(markup).toContain("Nearby area 1");
    expect(markup).toContain("Sample attraction 1 (fictional)");
    expect(markup).toContain("Synthetic demo fixture");
    expect(markup).toContain("Costs: not available from the current sources");
    expect(markup).toContain(
      "No provider-validated activities were available for this day.",
    );
  });

  it("shows current weather forecasts with their source", () => {
    const markup = renderToStaticMarkup(
      createElement(ItineraryDisplay, {
        itinerary: sampleItinerary([
          {
            date: "2026-11-07",
            area_id: "area-1",
            activities: [activity],
            weather: {
              forecast_date: "2026-11-07",
              timezone: "Demo/Fixture",
              weather_code: 3,
              temperature_max_c: 18,
              temperature_min_c: 11,
              precipitation_probability_max_pct: 25,
              data_status: "mock",
              source,
            },
          },
        ]),
      }),
    );

    expect(markup).toContain("Weather sample: 11–18°C");
    expect(markup).toContain("25% precipitation chance");
    expect(markup).toContain('href="https://example.test/demo/place"');
  });
});
