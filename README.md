# Popdle

A daily pop-culture Wordle (movies, TV shows, actors via TMDb) built as a PLG/growth case study —
not just a game, but an instrumented funnel: onboarding A/B test, activation tracking, and a
simulated premium paywall.

## Why this project

Built to mirror the responsibilities of a growth & monetization engineering role: full-stack
feature delivery, experimentation infrastructure, and using data to drive activation/conversion —
rather than just shipping a game.

## Architecture

- **Frontend:** React + TypeScript (Vite) — game board, stats/record page, onboarding flow with
  an A/B-tested variant, premium paywall modal.
- **Backend:** Python + FastAPI — game logic, daily word selection, event tracking, a homegrown
  feature-flag/assignment service (stands in for LaunchDarkly/Eppo).
- **Word source:** TMDb API (popular movies/TV/actors), filtered to clean single-word answers,
  with a curated fallback list for local dev without an API key.
- **Database:** Postgres — users, daily words, game attempts, events, experiments/assignments,
  subscriptions.
- **Growth instrumentation:**
  - `events` table captures the activation funnel: `signup -> game_started -> game_won ->
    paywall_viewed -> upgraded`.
  - `experiments`/`assignments` tables back a deterministic A/B assignment service
    (`onboarding_flow`: control vs. guided_tutorial).
  - `GET /admin/funnel` returns step-by-step conversion rates and an onboarding-variant
    activation breakdown — the kind of dashboard a growth team would actually look at.
- **Monetization (simulated):** a `subscriptions` table and paywall modal model a
  trial -> paid upgrade path (Stripe test-mode integration is a planned next step).

## Local setup

```bash
docker compose up -d          # Postgres + Redis
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add a TMDB_API_KEY (optional — falls back to curated words)
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

## Key endpoints

- `GET /game/today` — today's puzzle metadata (category, clue, word length — not the answer)
- `POST /game/guess` — submit a guess, get per-letter scoring
- `POST /events` — record a funnel event
- `GET /experiments/{key}/assignment?user_id=...` — get/assign an A/B variant
- `GET /admin/funnel` — funnel conversion + onboarding-variant activation rates
