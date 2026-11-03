# Local demo walkthrough

This walkthrough shows the current draft UI and the sourced travel-data APIs. The generated draft is still generic: it does not yet consume place, route, or weather results to construct its suggestions. Keep that distinction visible during a demo.

## Start the app

In one terminal, start the API:

```bash
cd apps/api
uv run --extra dev uvicorn app.main:app --reload
```

For live place lookups, set `GOOGLE_MAPS_API_KEY` in the API server environment before starting it. Enable Places API (New) and Routes API in the associated Google Cloud project. Keep the key server-side; do not use a `NEXT_PUBLIC_` variable.

In a second terminal, start the web app:

```bash
pnpm dev:web
```

## Walk through the draft and sourced data

1. Open `http://localhost:3000`, enter a destination, dates, budget, travelers, at least one interest, and a pace, then submit. The result is labeled `Demo · not verified`; it contains generic prompts and no verified venues.
2. Open `http://localhost:8000/docs` and call `GET /places/attractions` and `GET /places/restaurants`. Live results include provider IDs, coordinates, source links, retrieval times, and nearby-area grouping. If the Google key is missing, these endpoints return `503` and do not substitute fixtures.
3. Copy a returned place ID and coordinates into `POST /places/validate`. A matching provider record within 100 meters is returned with its validation status.
4. Use two returned coordinates with `POST /routes/estimate`. The duration is an estimate and includes its source.
5. Use one returned coordinate and a travel date with `POST /weather/forecast`. The result includes a source and retrieval time. If a forecast is unavailable, the response says so and contains no forecast values.

The API test suite uses clearly labeled mock providers to exercise this flow without network calls. It verifies that the generated draft remains marked unverified and that places, routes, and weather retain `data_status: "mock"`. These fixtures are test data only and must not be shown as real travel recommendations.

## Current live-demo blocker

`GOOGLE_MAPS_API_KEY` is not configured in the development environment, so live place and routing requests have not been demonstrated. Open-Meteo live requests were also not exercised. The walk-through describes how to run them once the relevant external access is configured; it does not claim the live data path has been verified.
