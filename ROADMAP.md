# 28-Day Roadmap

Each day is a goal, not a quota. Prefer one small, tested, reviewable increment. A day can be blocked by credentials; document the blocker and proceed with an independent task using clearly marked fixtures. Never create empty commits or merge a pull request with failing CI. The owner reviews each day's local changes and PR preview before any commit is pushed to GitHub.

## Week 1 — Foundation

- [x] Day 1: Initialize monorepo, frontend, backend, linting/formatting configuration, and README.
- [x] Day 2: Implement travel preferences form and validation.
- [x] Day 3: Create FastAPI endpoints and structured itinerary schemas.
- [ ] Day 4: Integrate LLM API and basic itinerary generation.
- [ ] Day 5: Add an Agent tool interface and structured tool outputs.
- [ ] Day 6: Implement itinerary display components.
- [ ] Day 7: Integration tests, bug fixes, and first milestone review.

## Week 2 — Real-world data

- [ ] Day 8: Integrate Places API.
- [ ] Day 9: Build attraction discovery tools.
- [ ] Day 10: Add restaurants and location validation.
- [ ] Day 11: Integrate routing and travel-time estimates.
- [ ] Day 12: Implement geographic grouping.
- [ ] Day 13: Add weather lookup and fallback handling.
- [ ] Day 14: End-to-end tests and real-data itinerary demo.

## Week 3 — Agent workflows

- [ ] Day 15: Create database schema and itinerary persistence.
- [ ] Day 16: Add itinerary history and retrieval.
- [ ] Day 17: Add conversational editing for an existing itinerary.
- [ ] Day 18: Implement partial-day itinerary regeneration.
- [ ] Day 19: Add budget estimates and constraint validation.
- [ ] Day 20: Add tool failures, retries, and timeouts.
- [ ] Day 21: End-to-end testing and workflow improvements.

## Week 4 — Quality and deployment

- [ ] Day 22: Create an evaluation dataset with at least 30 travel scenarios.
- [ ] Day 23: Implement agent evaluation metrics and automated evaluation scripts.
- [ ] Day 24: Add tracing, structured logging, latency, and token-cost measurement.
- [ ] Day 25: Add security checks, rate limiting, and input validation.
- [ ] Day 26: Add containerization, staging configuration, and deployment preparation.
- [ ] Day 27: Deploy a public demo only after owner approval; run smoke tests.
- [ ] Day 28: Finalize README, architecture diagram, screenshots, demo walkthrough, and benchmark report.

## Daily delivery checklist

1. Read `PROJECT.md`, `ROADMAP.md`, `AGENTS.md`, and repository status.
2. Inspect open GitHub issues and pull requests when repository access is configured.
3. Select the highest-priority unblocked task for the current milestone.
4. Review relevant code; add/update tests and implement the smallest complete feature.
5. Run formatting, linting, type checks, and relevant tests.
6. Present a daily review packet: changes, tests, blockers, a diff, and a proposed PR title and description. Label it as a PR preview; do not create a GitHub commit, push, or real PR before the owner's explicit approval.
7. After approval, commit the reviewed changes, push the feature branch, and open the PR. If GitHub is not connected, keep work local and report the exact missing setup. Do not merge failing CI.

Production deployment, billing changes, database-destructive operations, and credential changes require explicit owner approval.

Day 4 note: `OPENAI_API_KEY` is not configured in the development environment. The local implementation provides a deterministic demo endpoint for integration testing; live LLM generation remains blocked and Day 4 stays unchecked until the LLM provider is wired and exercised.
