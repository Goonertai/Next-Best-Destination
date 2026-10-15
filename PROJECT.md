# AI Travel Planning Agent

## Product goal

Build a practical, personalized travel-planning application that creates editable, multi-day itineraries from user preferences and verified real-world place information. The agent must distinguish sourced facts from estimates and must never invent place details, availability, prices, opening hours, or travel-time estimates.

## MVP users and inputs

Travelers provide a destination, travel dates, total budget and currency, group size, interests, preferences, and desired pace. The application returns a structured itinerary by day with attractions, restaurants, transportation suggestions, estimated costs, and source information. Travelers can revise plans in natural language and retrieve saved itineraries.

## Technical direction

- Web: Next.js, TypeScript, Tailwind CSS
- API: Python, FastAPI, Pydantic
- Agent: OpenAI Agents SDK behind an orchestration boundary
- Storage: PostgreSQL, accessed through repository interfaces
- External data: Google Maps Platform and a weather provider, isolated behind provider interfaces
- Quality: pytest, Vitest, Playwright, evaluation scenarios, GitHub Actions
- Deployment targets: Vercel for web; Render or Railway for API and PostgreSQL
- Operations: structured logs, agent traces, latency and token-cost metrics

## Architecture boundaries

`apps/web` owns the responsive user interface and API client. `apps/api` owns HTTP endpoints, schemas, business validation, agent orchestration, provider tools, persistence, and evaluations. Provider interfaces and fixtures allow tests to run without paid API calls. Keep this a modular monolith; add no services or abstractions without a concrete need.

## Safety and data integrity

- Treat externally sourced information as time-sensitive and retain its source and retrieval time.
- Do not present estimated costs or durations as verified facts.
- Validate place IDs and coordinates before an item is marked verified.
- Handle provider timeouts, errors, and missing credentials with explicit user-facing status.
- Never log secrets or unnecessary personal data; never commit credentials.
- Production deployment, billing changes, credential changes, and destructive database operations require owner approval.

## MVP acceptance goals

1. Collect and validate traveler preferences.
2. Generate a structured itinerary with a tool-using agent and real place data.
3. Group activities geographically and use supported routing data for travel estimates.
4. Clearly label estimates and expose sources for sourced details.
5. Revise an existing itinerary conversationally and persist it in PostgreSQL.
6. Provide a responsive itinerary UI and graceful provider-failure behavior.
7. Run automated tests, a 30-scenario evaluation suite, CI, and a documented demo.

See [ROADMAP.md](ROADMAP.md) for the 28-day delivery plan.
