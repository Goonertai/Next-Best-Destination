import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ItineraryDisplay } from "./ItineraryDisplay";

describe("ItineraryDisplay", () => {
  it("shows each dated suggestion and the demo verification notice", () => {
    const markup = renderToStaticMarkup(
      createElement(ItineraryDisplay, {
        itinerary: {
          destination: "Montreal",
          generation_mode: "demo",
          is_complete_itinerary: false,
          uses_verified_place_data: false,
          notice: "No real venues have been retrieved or verified.",
          days: [
            {
              date: "2026-11-07",
              suggestions: ["Consider a history-focused activity."],
            },
            { date: "2026-11-08", suggestions: ["Explore an art theme."] },
          ],
        },
      }),
    );

    expect(markup).toContain("A few ideas for Montreal.");
    expect(markup).toContain("Demo · not verified");
    expect(markup).toContain("No real venues have been retrieved or verified.");
    expect(markup).toContain("Saturday, November 7");
    expect(markup).toContain("Sunday, November 8");
    expect(markup).toContain("Consider a history-focused activity.");
    expect(markup).toContain("Explore an art theme.");
  });

  it("shows an explicit empty state for a day without prompts", () => {
    const markup = renderToStaticMarkup(
      createElement(ItineraryDisplay, {
        itinerary: {
          destination: "Montreal",
          generation_mode: "demo",
          is_complete_itinerary: false,
          uses_verified_place_data: false,
          notice: "Generic ideas only.",
          days: [{ date: "2026-11-07", suggestions: [] }],
        },
      }),
    );

    expect(markup).toContain("No suggestions for this day.");
  });
});
