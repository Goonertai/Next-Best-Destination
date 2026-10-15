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

Day 1 establishes the monorepo, development scripts, FastAPI health endpoint, and Next.js landing page. Later roadmap tasks add trip planning behavior, provider integrations, persistence, and deployment configuration.
