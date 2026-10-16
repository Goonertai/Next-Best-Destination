import Link from "next/link";
import { TripPreferencesForm } from "./TripPreferencesForm";

const steps = [
  {
    number: "01",
    title: "Tell us what matters",
    detail: "Your dates, budget, interests, and preferred pace shape the plan.",
  },
  {
    number: "02",
    title: "Explore with context",
    detail:
      "Places and routes will include sources, so you can check the details.",
  },
  {
    number: "03",
    title: "Make it yours",
    detail: "Ask for a change and refine your itinerary as you go.",
  },
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <nav className="topbar" aria-label="Main navigation">
        <Link className="brand" href="/" aria-label="Waypoint home">
          <span className="brand-mark">W</span> waypoint
        </Link>
        <span className="topbar-note">A more considered way to go</span>
        <a
          className="nav-link focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#df7049]"
          href="#how-it-works"
        >
          How it works <span aria-hidden="true">↘</span>
        </a>
      </nav>

      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="eyebrow-dot" /> YOUR NEXT TRIP, THOUGHTFULLY
            PLANNED
          </p>
          <h1 id="hero-title">
            Go somewhere
            <br />
            <em>worth remembering.</em>
          </h1>
          <p className="hero-description">
            A travel plan shaped around your pace, your people, and the places
            you actually want to see.
          </p>
          <a className="primary-button" href="#trip-preferences">
            Start planning <span aria-hidden="true">→</span>
          </a>
          <p className="hero-footnote">Your plan. Your pace. No guesswork.</p>
        </div>
        <div
          className="hero-art"
          aria-label="Illustration of a sunlit coastal destination"
        >
          <div className="sun" />
          <div className="art-label">
            <span>36° 27′ N</span>
            <span>YOUR NEXT CHAPTER</span>
          </div>
          <div className="hill hill-back" />
          <div className="hill hill-front" />
          <div className="water" />
          <div className="art-stamp">
            <span>
              TAKE
              <br />
              THE
              <br />
              SCENIC
              <br />
              ROUTE
            </span>
            <span className="stamp-arrow">↘</span>
          </div>
          <div className="art-caption">A little room for wonder.</div>
        </div>
      </section>

      <section
        className="planner-section"
        id="trip-preferences"
        aria-labelledby="planner-title"
      >
        <div className="planner-heading">
          <p className="eyebrow">START WITH THE DETAILS</p>
          <h2 id="planner-title">Tell us about your trip.</h2>
          <p>
            Share your dates, budget, and interests. We will validate the setup
            before connecting itinerary generation.
          </p>
        </div>
        <TripPreferencesForm />
      </section>

      <section
        className="steps"
        id="how-it-works"
        aria-label="How Waypoint works"
      >
        <div className="steps-heading">
          <p className="eyebrow">A BETTER KIND OF ITINERARY</p>
          <p>
            Good trips leave space
            <br />
            for the unexpected.
          </p>
        </div>
        {steps.map((step) => (
          <article className="step" key={step.number}>
            <span>{step.number}</span>
            <h2>{step.title}</h2>
            <p>{step.detail}</p>
          </article>
        ))}
      </section>
      <footer>
        <span>waypoint</span>
        <span>Thoughtful plans, one trip at a time.</span>
        <span>© 2026 Waypoint</span>
      </footer>
    </main>
  );
}
