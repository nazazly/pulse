# Multi-Sport & Esports Hub (Backend)

An asynchronous backend service aggregating schedules, live scores, and match results across esports (CS2, Valorant) and traditional sports (Football/Premier League, Tennis, UFC).

## Tech Stack
- **Language & Framework:** Python 3.11+, FastAPI
- **Database:** PostgreSQL (User accounts, team preferences, match logs)
- **Caching & Rate Limiting:** Redis (Live scoreboards, external API protection)
- **Data Ingestion:** PandaScore API (Esports), Football-Data.org (Football)

## Initial Scope (MVP)
- **User & Preference Management:**
  - Create account & login via JWT.
  - Favorite/shortlist teams across supported sports.
  - Query a personalized feed containing only favorited clubs/teams.
- **Match Aggregation & Details:**
  - Explore live, past (last 6h), and upcoming fixtures by discipline.
  - Dynamic team profile showing current roster and recent form.

## Local Setup
1. Activate virtual environment:
   ```bash
   source .venv/bin/activate