# Local POC walkthrough

The local POC runs without external credentials in sample mode. Sample places, coordinates, route durations, and weather values are fictional fixtures, marked as mock, and must not be used to make real travel decisions.

## Start the apps

In terminal 1:

```bash
cd apps/api
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

In terminal 2, from the repository root:

```bash
pnpm install
pnpm dev:web
```

Open `http://localhost:3000`. Saved sample itineraries are stored in `apps/api/data/itineraries.db` by default.

## Try a complete sample itinerary

1. Enter a destination, dates, total budget, travelers, interests, and pace.
2. Choose **Sample demo data (fictional)** and click **Generate itinerary**.
3. Confirm the result is labeled **Sample data · fictional**. Each day shows fictional sample places, a nearby-area label, a sample route estimate, and sample weather with source labels. The cost line says it is unavailable from the current sources.
4. In **Ask to change this plan**, try `remove Sample attraction 1 (fictional)` or `move Sample attraction 2 (fictional) to day 2`. In sample mode without an OpenAI key, only unambiguous remove/move commands for existing activities are accepted. Unsupported requests return an explanation and leave the plan unchanged.
5. Click **Save itinerary**. The saved trip appears under **Saved trips**. Refresh the page and open it again.
6. Click **Copy share link** and open the copied URL in a new tab. Anyone with the unlisted link can view that saved snapshot. Edits create an unsaved copy; save again to get a new immutable snapshot and share link.

## Try live provider data

Set `GOOGLE_MAPS_API_KEY` in the API server's environment before starting it. The associated Google Cloud project must have Places API (New) and Routes API enabled. Keep the key server-side.

Choose **Live Google places** in the form. The API searches attraction and restaurant listings using the selected interests and preferences, validates each scheduled place ID and coordinate against Place Details, groups results by nearby area, and requests route estimates between activities. Forecasts come from Open-Meteo. The UI links each listing and forecast to its source. Route durations are explicitly marked as estimates.

If the Google key is absent or the provider request fails, the live request returns an explicit error and does not substitute sample venues. Open `http://localhost:8000/docs` to inspect the individual discovery, validation, routing, and weather endpoints.

## Try Agents SDK edit interpretation

Set `OPENAI_API_KEY` in the API server environment. The edit agent uses a tool to read the current activity IDs and is instructed to only remove or move existing activities. It cannot create a venue, price, opening hour, route, or weather fact. Without this key, the sample mode uses the constrained rule-based remove/move commands above.

## Configure PostgreSQL

Local development uses SQLite unless `DATABASE_URL` is set. To use PostgreSQL, set a server-side value such as `postgresql://user:password@localhost:5432/travel_agent` before starting the API. The POC creates its table with SQLAlchemy metadata on first use; schema migrations are not set up yet.

## POC limits

- The OpenAI and Google live paths require owner-provided credentials and were not exercised during development.
- Sample mode is only for testing the interface and workflows. Its fictional data is not real travel information.
- No current prices or opening hours are provided; the app says when price data is unavailable.
- This POC has no sign-in. Saved-trip history is shared by the configured database, and anyone with an itinerary link can view that snapshot. Keep it local/private until authentication and per-user access controls are added.
- Do not deploy it as a public travel service yet.
