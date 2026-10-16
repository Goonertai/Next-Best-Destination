# Agent Instructions

## Start of each work session

- Read `PROJECT.md`, `ROADMAP.md`, this file, and `git status` before changing code.
- If GitHub access is configured, inspect open issues and pull requests before choosing work.
- Select the highest-priority unblocked roadmap task; do not assume a scheduled run happened if it did not.

## Engineering practices

- Keep API endpoints, agent orchestration, external providers, business validation, repositories, UI, and evaluation code in separate, understandable modules.
- Use provider interfaces and deterministic fixtures so tests do not require paid external API calls.
- Never fabricate verified place details, booking availability, prices, opening hours, or travel-time estimates. Label all estimates and retain source metadata.
- Add or update meaningful tests for behavior changes. Run applicable formatters, linters, type checks, and tests; report exact commands and outcomes.
- Document external credentials and setup using variable names only. Never add secret values, confidential information, or unnecessary personal data.
- Make each day's changes reviewable locally and run the relevant checks before requesting approval.
- Before the owner approves that day's review packet, do not commit, push, or open a real GitHub PR. A GitHub PR requires a pushed commit, so provide a clearly labeled PR preview with the proposed title, description, change summary, test results, and diff instead.
- After explicit owner approval, create a meaningful commit, push the feature branch, and open the PR. Do not merge it unless separately asked, and never merge when CI fails.
- If the repository remote or GitHub authorization is unavailable, keep the work local and report the exact missing setup. Never claim a push or PR exists when it does not.
- Do not make empty commits to satisfy a daily cadence.

## Approval boundaries

Do not perform production deployment, billing changes, credential changes, or destructive database operations without explicit owner approval. If external credentials or permissions are missing, document the blocker and continue with an independent task using clearly labeled mock fixtures.

## Completion report

Summarize changes, test results, blockers, and next steps. Label unapproved PR material as a preview. Never claim a push, PR, deployment, or test passed unless it actually did.
