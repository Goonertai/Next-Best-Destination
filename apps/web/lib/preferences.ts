export const TRAVEL_INTERESTS = [
  "Food",
  "Nature",
  "History",
  "Architecture",
  "Art",
  "Shopping",
  "Nightlife",
] as const;

export const TRAVEL_PACES = ["relaxed", "balanced", "packed"] as const;

export type TravelPace = (typeof TRAVEL_PACES)[number];

export type TravelPreferencesInput = {
  destination: string;
  startDate: string;
  endDate: string;
  totalBudget: string;
  currency: string;
  travelers: string;
  interests: string[];
  preferences: string;
  pace: string;
};

export type TravelPreferencesErrors = Partial<
  Record<keyof TravelPreferencesInput, string>
>;

function isValidDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;

  const date = new Date(`${value}T00:00:00Z`);
  return (
    !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === value
  );
}

export function validateTravelPreferences(
  input: TravelPreferencesInput,
): TravelPreferencesErrors {
  const errors: TravelPreferencesErrors = {};

  if (!input.destination.trim()) {
    errors.destination = "Enter a destination.";
  }

  if (!isValidDate(input.startDate)) {
    errors.startDate = "Enter a valid start date.";
  }

  if (!isValidDate(input.endDate)) {
    errors.endDate = "Enter a valid end date.";
  } else if (isValidDate(input.startDate) && input.endDate <= input.startDate) {
    errors.endDate = "The end date must be after the start date.";
  }

  const budget = Number(input.totalBudget);
  if (!input.totalBudget.trim() || !Number.isFinite(budget) || budget <= 0) {
    errors.totalBudget = "Enter a budget greater than zero.";
  }

  if (!input.currency.trim()) {
    errors.currency = "Choose a currency.";
  }

  if (!/^\d+$/.test(input.travelers)) {
    errors.travelers = "Enter a whole number of travelers.";
  } else {
    const travelerCount = Number(input.travelers);
    if (travelerCount < 1 || travelerCount > 20) {
      errors.travelers = "Enter between 1 and 20 travelers.";
    }
  }

  if (input.interests.length === 0) {
    errors.interests = "Choose at least one interest.";
  }

  if (!TRAVEL_PACES.includes(input.pace as TravelPace)) {
    errors.pace = "Choose a travel pace.";
  }

  return errors;
}
