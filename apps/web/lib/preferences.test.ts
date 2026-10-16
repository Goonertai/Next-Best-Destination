import { describe, expect, it } from "vitest";
import {
  validateTravelPreferences,
  type TravelPreferencesInput,
} from "./preferences";

const validPreferences: TravelPreferencesInput = {
  destination: "Lisbon",
  startDate: "2027-05-10",
  endDate: "2027-05-15",
  totalBudget: "2500",
  currency: "CAD",
  travelers: "2",
  interests: ["Food", "History"],
  preferences: "Vegetarian options preferred",
  pace: "balanced",
};

describe("validateTravelPreferences", () => {
  it("accepts complete, valid trip preferences", () => {
    expect(validateTravelPreferences(validPreferences)).toEqual({});
  });

  it("requires the core trip details and at least one interest", () => {
    const errors = validateTravelPreferences({
      ...validPreferences,
      destination: "  ",
      startDate: "",
      endDate: "",
      totalBudget: "0",
      currency: "",
      travelers: "",
      interests: [],
      pace: "",
    });

    expect(errors).toMatchObject({
      destination: expect.any(String),
      startDate: expect.any(String),
      endDate: expect.any(String),
      totalBudget: expect.any(String),
      currency: expect.any(String),
      travelers: expect.any(String),
      interests: expect.any(String),
      pace: expect.any(String),
    });
  });

  it("rejects invalid calendar dates and a non-increasing date range", () => {
    expect(
      validateTravelPreferences({
        ...validPreferences,
        startDate: "2027-02-29",
        endDate: "2027-03-01",
      }),
    ).toMatchObject({
      startDate: expect.any(String),
    });

    expect(
      validateTravelPreferences({
        ...validPreferences,
        startDate: "2027-05-10",
        endDate: "2027-05-10",
      }).endDate,
    ).toBe("The end date must be after the start date.");
  });

  it("requires a positive budget and an integer group size from 1 to 20", () => {
    const errors = validateTravelPreferences({
      ...validPreferences,
      totalBudget: "NaN",
      travelers: "2.5",
    });
    expect(errors.totalBudget).toBe("Enter a budget greater than zero.");
    expect(errors.travelers).toBe("Enter a whole number of travelers.");

    expect(
      validateTravelPreferences({ ...validPreferences, travelers: "21" })
        .travelers,
    ).toBe("Enter between 1 and 20 travelers.");
  });
});
