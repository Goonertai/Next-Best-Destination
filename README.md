# AI Travel Planning Agent

A production-minded full-stack MVP for personalized, source-aware travel itineraries. The 28-day plan and autonomous engineering rules are in [ROADMAP.md](ROADMAP.md) and [AGENTS.md](AGENTS.md).

## Repository layout

```text
apps/
  api/       FastAPI service, domain logic, providers, agent, and tests
  web/       Next.js app
```

## Prerequisites

- Node.js 22+ and pnpm 11.25.0
- Python 3.11+
- PostgreSQL is optional for local development; SQLite is the default

## Local development

```bash
pnpm install
pnpm dev:web
```

For the API, install its dependencies and start FastAPI:

```bash
cd apps/api
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Run API tests with `cd apps/api && uv run --extra dev pytest -q`. Run web checks from the repository root with `pnpm lint`, `pnpm typecheck`, `pnpm test:web`, and `pnpm build:web`.

## Daily review and GitHub approval

Each daily run produces tested local changes and a review packet with a diff, test results, and a proposed PR title and description. Because a real GitHub PR requires a commit pushed to a remote branch, no commit, push, or PR is created until the owner approves that day's review packet. After approval and GitHub access are configured, the feature branch is pushed and the PR link is shared.

Set environment variables in the API server process; FastAPI does not read `.env` automatically. Never commit credentials.

The app has two itinerary modes. Sample mode works without credentials and uses fictional records clearly labeled as mock. Live mode uses server-side Google Places and Routes and returns an explicit error when `GOOGLE_MAPS_API_KEY` is missing; it never falls back to sample data. Keep that key on the API server and never use a `NEXT_PUBLIC_` prefix. The Google Cloud project needs Places API (New) and Routes API enabled.

Set `OPENAI_API_KEY` in the API process to use the OpenAI Agents SDK to interpret remove/move edit requests. Without the key, sample mode accepts explicit remove/move commands through a constrained local parser. It does not invent new venues. Live Google and Open-Meteo requests were not made during development.

Saved trips use a local SQLite database at `apps/api/data/itineraries.db` when the API is started from `apps/api`. Set `DATABASE_URL` to a PostgreSQL connection string to use PostgreSQL. The API creates the POC schema on startup. A public deployment still needs user authentication and access controls before storing private itineraries.

For local web-to-API requests, the API allows `http://localhost:3000` by default. Set `CORS_ALLOWED_ORIGINS` to a comma-separated list of exact web app origins when using a different local or staging origin.

## Current status

The web form now generates a multi-day sample plan by day, saves and reopens snapshots, copies a share link, and supports safe remove/move edits. Sample locations, routes, and weather are fictional and visibly marked as mock. With Google credentials, `POST /itineraries/plan` retrieves and validates provider places, groups nearby activities, estimates routes, and fetches weather. Prices and opening hours are not invented; when the sources do not provide prices, the UI says they are unavailable.

### Run the local POC

Follow the [local POC walkthrough](docs/demo-walkthrough.md). Sample mode requires no API key and supports itinerary generation, editing, saving, reopening, and sharing. Its data is fictional.

### Discover real places and estimate routes

With `GOOGLE_MAPS_API_KEY` configured for the API, use `GET /places/attractions?destination=Montreal` or `GET /places/restaurants?destination=Montreal`. Each result includes the Google Place ID, coordinates, a Maps URL, and provider retrieval time. Search responses also include `groups`: places within 1,500 meters in a straight line of each group's anchor share an area. This area grouping does not represent road distance or a route estimate. `POST /places/validate` checks an ID with Place Details and compares the supplied coordinates with the provider location using a 100-meter tolerance. `POST /routes/estimate` calls Routes API Compute Routes and returns duration and distance as an estimate with its source.

Agents SDK tools are registered for attraction search, restaurant search, place validation, route estimation, and weather. Automated tests use clearly labeled synthetic fixtures and mocked HTTP responses; they never contact paid APIs or present fixture locations as real.

### Look up a daily weather forecast

Send sourced coordinates and a date to `POST /weather/forecast`, for example `{"coordinates":{"latitude":43.6532,"longitude":-79.3832},"forecast_date":"2026-11-10"}`. A returned forecast includes the provider's weather code, daily high/low in Celsius, maximum precipitation probability, local timezone, source, and retrieval time. The endpoint returns `data_status: "unavailable"` and no forecast when the provider fails or has no value for the date, so the planner can continue without making weather assumptions. The automated tests use mock data only.

This integration uses the [Open-Meteo Forecast API](https://open-meteo.com/en/docs). Its standard endpoint requires no API key for non-commercial use and provides forecasts up to 16 days; Open-Meteo requires attribution. Check its current [usage and pricing terms](https://open-meteo.com/en/pricing) before a public commercial deployment. No live weather request was made during development.

### Run the local demo

Follow the [local demo walkthrough](docs/demo-walkthrough.md) to exercise the draft UI, then use the API docs to inspect sourced places, validation, routes, and weather. The walkthrough identifies which steps need a Google Maps API key and distinguishes the generic draft from verified provider data.
