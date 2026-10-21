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
- PostgreSQL will be added when persistence is implemented

## Local development

```bash
pnpm install
pnpm dev:web
```

For the API, create a virtual environment and install its development dependencies:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Run API tests with `cd apps/api && pytest`; run web checks from the repository root with `pnpm lint`, `pnpm typecheck`, and `pnpm test:web`.

## Daily review and GitHub approval

Each daily run produces tested local changes and a review packet with a diff, test results, and a proposed PR title and description. Because a real GitHub PR requires a commit pushed to a remote branch, no commit, push, or PR is created until the owner approves that day's review packet. After approval and GitHub access are configured, the feature branch is pushed and the PR link is shared.

Copy `.env.example` to `.env` when integrations are introduced. Do not commit secrets. No external API credentials are required for the Day 1 health check.

## Current status

Day 1 established the monorepo, development scripts, FastAPI health endpoint, and Next.js landing page. Day 2 adds a validated trip-preferences form. Day 3 adds typed itinerary and preference schemas plus a preferences-validation endpoint. Day 4 adds a deterministic demo draft endpoint; live LLM generation is blocked until `OPENAI_API_KEY` is configured. Day 5 adds a typed OpenAI Agents SDK tool boundary and a deterministic endpoint for generic activity prompts. Real place discovery, persistence, and deployment remain on the roadmap.

### Try the demo draft endpoint

Start the API with `cd apps/api && uv run --extra dev uvicorn app.main:app --reload`, then open `http://localhost:8000/docs` and submit the preferences schema to `POST /itineraries/generate`. The response contains generic interest-based prompts only. It is marked as an incomplete demo and contains no retrieved or verified venues, opening hours, prices, routes, or weather.

### Try the structured Agent tool fixture

With the API running, submit `{"destination":"Montreal","interests":["Food","History"]}` to `POST /itineraries/activity-ideas` in `/docs`. The response includes typed prompts and `data_status: "not_retrieved"`; the endpoint uses no external services and does not claim specific places were verified. The SDK agent can be constructed without credentials, but running it through a live model requires `OPENAI_API_KEY`.
