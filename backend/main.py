from fastapi import FastAPI, HTTPException, Query
from typing import List
from schemas import NormalisedMatch, SportType
from services import fetch_live_team_matches

app = FastAPI(
    title = "Pulse API",
    description = "Unified Multi-Sport & Esports Match Aggregator",
    version = "0.1.0"
)

# Known demo IDs for quick recruiter demonstration
DEMO_TEAMS = {
    "navi": {"id": 3216, "sport": SportType.CS2},
    "prx": {"id": 128917, "sport": SportType.VALORANT}
}

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Pulse Backend"}

@app.get("/api/teams/{team_id}/matches", response_model = List[NormalisedMatch])
def get_team_matches(
    team_id: int,
    sport: SportType = Query(..., description = "Sport category: CS2, Valorant, or Football"),
    limit: int = Query(5, ge=1, le=10)
):
    """
    Fetches and normalises real-time fixtures & results for any team ID.
    """
    matches = fetch_live_team_matches(team_id=team_id, sport=sport, limit=limit)
    if not matches:
        raise HTTPException(status_code=404, detail="No matches found or upstream API error.")
    return matches

@app.get("/api/feed/demo", response_model=List[NormalisedMatch])
def get_demo_feed():
    """
    Aggregated feed of favourite teams (NAVI CS2, Paper Rex Valorant) in one unified list.
    """
    feed = []
    feed.extend(fetch_live_team_matches(DEMO_TEAMS["navi"]["id"], DEMO_TEAMS["navi"]["sport"], limit=3))
    feed.extend(fetch_live_team_matches(DEMO_TEAMS["prx"]["id"], DEMO_TEAMS["prx"]["sport"], limit=3))
    return feed