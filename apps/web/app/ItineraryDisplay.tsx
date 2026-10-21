import type { ItineraryDraft } from "../lib/api";

type ItineraryDisplayProps = {
  itinerary: ItineraryDraft;
};

function formatItineraryDate(value: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

export function ItineraryDisplay({ itinerary }: ItineraryDisplayProps) {
  return (
    <section
      className="itinerary-panel"
      aria-labelledby="itinerary-results-title"
    >
      <div className="itinerary-heading">
        <div>
          <p className="eyebrow">YOUR FIRST DRAFT</p>
          <h2 id="itinerary-results-title">
            A few ideas for {itinerary.destination}.
          </h2>
        </div>
        <span className="itinerary-status">Demo · not verified</span>
      </div>

      <p className="itinerary-notice" role="note">
        {itinerary.notice}
      </p>

      <ol className="itinerary-days">
        {itinerary.days.map((day, index) => (
          <li className="itinerary-day" key={day.date}>
            <div className="itinerary-day-heading">
              <span className="itinerary-day-number">
                DAY {String(index + 1).padStart(2, "0")}
              </span>
              <h3>
                <time dateTime={day.date}>{formatItineraryDate(day.date)}</time>
              </h3>
            </div>
            {day.suggestions.length > 0 ? (
              <ul className="itinerary-suggestions">
                {day.suggestions.map((suggestion) => (
                  <li key={suggestion}>
                    <span aria-hidden="true">↗</span>
                    <p>{suggestion}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="itinerary-empty-day">
                No suggestions for this day.
              </p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
