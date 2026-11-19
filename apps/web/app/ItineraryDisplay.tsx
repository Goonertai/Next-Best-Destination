import type { Itinerary } from "../lib/api";

type ItineraryDisplayProps = {
  itinerary: Itinerary;
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function ItineraryDisplay({ itinerary }: ItineraryDisplayProps) {
  const isDemo = itinerary.generation_mode === "demo";

  return (
    <section
      className="itinerary-panel"
      aria-labelledby="itinerary-results-title"
    >
      <div className="itinerary-heading">
        <div>
          <p className="eyebrow">YOUR ITINERARY</p>
          <h2 id="itinerary-results-title">
            Your trip to {itinerary.destination}.
          </h2>
        </div>
        <span className={`itinerary-status${isDemo ? " is-demo" : " is-live"}`}>
          {isDemo
            ? "Sample data · fictional"
            : "Live places · estimates labeled"}
        </span>
      </div>

      <p className="itinerary-notice" role="note">
        {itinerary.notice}
      </p>
      {itinerary.warnings.length > 0 && (
        <div className="itinerary-warnings" role="status">
          <strong>Plan notes</strong>
          <ul>
            {itinerary.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="itinerary-cost-note">
        Costs:{" "}
        {itinerary.total_estimated_cost
          ? `estimated total ${itinerary.total_estimated_cost.amount} ${itinerary.total_estimated_cost.currency}`
          : "not available from the current sources"}
      </p>

      <ol className="itinerary-days">
        {itinerary.days.map((day, index) => (
          <li className="itinerary-day" key={day.date}>
            <div className="itinerary-day-heading">
              <span className="itinerary-day-number">
                DAY {String(index + 1).padStart(2, "0")}
              </span>
              <h3>
                <time dateTime={day.date}>{formatDate(day.date)}</time>
              </h3>
              {day.area_id && (
                <span className="itinerary-area">
                  Nearby area {day.area_id.replace("area-", "")}
                </span>
              )}
            </div>

            {day.weather && (
              <p className="itinerary-weather">
                Weather{" "}
                {day.weather.data_status === "mock" ? "sample" : "forecast"}:{" "}
                {day.weather.temperature_min_c}–{day.weather.temperature_max_c}
                °C
                {day.weather.precipitation_probability_max_pct !== null &&
                  ` · ${day.weather.precipitation_probability_max_pct}% precipitation chance`}
                {" · "}
                <a
                  href={day.weather.source.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {day.weather.source.provider} source
                </a>
              </p>
            )}

            {day.activities.length > 0 ? (
              <ol className="itinerary-activities">
                {day.activities.map((activity) => (
                  <li
                    className="itinerary-activity"
                    key={`${day.date}-${activity.place.place_id}`}
                  >
                    <div className="activity-time">
                      <time dateTime={activity.start_time}>
                        {formatTime(activity.start_time)}
                      </time>
                      <span>{formatTime(activity.end_time)}</span>
                    </div>
                    <div className="activity-main">
                      <span className="activity-category">
                        {activity.category}
                      </span>
                      <h4>{activity.place.name}</h4>
                      <p>{activity.description}</p>
                      <a
                        href={activity.place.source.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Source: {activity.place.source.provider}
                      </a>
                      {!activity.place_is_verified && !isDemo && (
                        <span className="activity-unverified">
                          Place needs verification
                        </span>
                      )}
                    </div>
                    {activity.travel_from_previous && (
                      <p className="activity-route">
                        {activity.travel_from_previous.minutes} min{" "}
                        {activity.travel_from_previous.mode.toLowerCase()} ·
                        estimate
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="itinerary-empty-day">
                No provider-validated activities were available for this day.
              </p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
