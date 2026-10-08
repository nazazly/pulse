import os
from datetime import datetime
from pathlib import Path
import zoneinfo
import requests
from dotenv import load_dotenv

from schemas import NormalisedMatch, SportType, MatchStatus, TeamBasic

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("PANDASCORE_API_KEY")
BASE_URL = "https://api.pandascore.co"
SGT_TZ = zoneinfo.ZoneInfo("Asia/Singapore")

def format_to_sgt(utc_iso_string: str | None) -> str:
    if not utc_iso_string:
        return "TBD"
    utc_dt = datetime.fromisoformat(utc_iso_string.replace("Z", "+00:00"))
    sgt_dt = utc_dt.astimezone(SGT_TZ)
    return sgt_dt.strftime("%d %b %Y, %H:%M SGT")

def map_match_status(raw_status: str | None) -> MatchStatus:
    status_lower = (raw_status or "").lower()
    if status_lower in ["running", "live"]:
        return MatchStatus.LIVE
    elif status_lower in ["finished", "settled"]:
        return MatchStatus.FINISHED
    return MatchStatus.UPCOMING

def parse_pandascore_match(raw_match: dict, sport: SportType) -> NormalisedMatch:
    opponents = raw_match.get("opponents", [])

    # Extract home team details
    if len(opponents) > 0 and opponents[0].get("opponent"):
        home_raw = opponents[0]["opponent"]
        home_team = TeamBasic(
            id = str(home_raw.get("id", "0")),
            name = home_raw.get("name", "TBD"),
            acronym = home_raw.get("acronym"),
            logo_url = home_raw.get("image_url")
        )
    else:
        home_team = TeamBasic(id="0", name="TBD")

    # Extract away team details
    if len(opponents) > 1 and opponents[1].get("opponent"):
        away_raw = opponents[1]["opponent"]
        away_team = TeamBasic(
            id=str(away_raw.get("id", "0")),
            name=away_raw.get("name", "TBD"),
            acronym=away_raw.get("acronym"),
            logo_url=away_raw.get("image_url")
        )
    else:
        away_team = TeamBasic(id="0", name="TBD")

    # Extract scores if match is finished or live
    home_score = 0
    away_score = 0
    for res in raw_match.get("results", []):
        if str(res.get("team_id")) == home_team.id:
            home_score = res.get("score", 0)
        elif str(res.get("team_id")) == away_team.id:
            away_score = res.get("score", 0)

    winner_id = raw_match.get("winner_id")

    return NormalisedMatch(
        id=f"{sport.value}-{raw_match.get('id')}",
        sport=sport,
        tournament_name=raw_match.get("league", {}).get("name", "Unknown Tournament"),
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        status=map_match_status(raw_match.get("status")),
        scheduled_at_sgt=format_to_sgt(raw_match.get("scheduled_at")),
        winner_team_id=str(winner_id) if winner_id else None
    )

def fetch_live_team_matches(team_id: int, sport: SportType, limit: int = 5) -> list[NormalisedMatch]:
    if not API_KEY:
        return []

    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {
        "token": API_KEY.strip(),
        "sort": "-scheduled_at",
        "page[size]": limit
    }

    res = requests.get(url, params=params)
    if res.status_code != 200:
        return []

    return [parse_pandascore_match(m, sport) for m in res.json()]

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
FOOTBALL_BASE_URL = "https://api.football-data.org/v4"

def map_football_status(raw_status: str | None) -> MatchStatus:
    status = (raw_status or "").upper()
    if status in ["IN_PLAY", "PAUSED"]:
        return MatchStatus.LIVE
    elif status in ["FINISHED", "AWARDED"]:
        return MatchStatus.FINISHED
    return MatchStatus.UPCOMING

def parse_football_match(raw_match: dict) -> NormalisedMatch:
    home_raw = raw_match.get("homeTeam", {})
    away_raw = raw_match.get("awayTeam", {})
    score_data = raw_match.get("score", {})

    # Check fullTime first, fallback to regularTime if present
    full_time = score_data.get("fullTime") or {}
    regular_time = score_data.get("regularTime") or {}

    home_score = full_time.get("home")
    if home_score is None:
        home_score = regular_time.get("home", 0)

    away_score = full_time.get("away")
    if away_score is None:
        away_score = regular_time.get("away", 0)

    # Determine winner team ID or DRAW
    winner_str = score_data.get("winner")
    winner_id = None
    if winner_str == "HOME_TEAM":
        winner_id = str(home_raw.get("id"))
    elif winner_str == "AWAY_TEAM":
        winner_id = str(away_raw.get("id"))
    elif winner_str == "DRAW":
        winner_id = "DRAW"

    return NormalisedMatch(
        id = f"football-{raw_match.get('id')}",
        sport = SportType.FOOTBALL,
        tournament_name = raw_match.get("competition", {}).get(
            "name", "Premier League"
        ),
        home_team = TeamBasic(
            id = str(home_raw.get("id", "0")),
            name = home_raw.get("name", "TBD"),
            acronym = home_raw.get("tla"),
            logo_url = home_raw.get("crest"),
        ),
        away_team = TeamBasic(
            id = str(away_raw.get("id", "0")),
            name = away_raw.get("name", "TBD"),
            acronym = away_raw.get("tla"),
            logo_url = away_raw.get("crest"),
        ),
        home_score = home_score or 0,
        away_score = away_score or 0,
        status = map_football_status(raw_match.get("status")),
        scheduled_at_sgt = format_to_sgt(raw_match.get("utcDate")),
        winner_team_id = winner_id,
    )

def fetch_live_football_matches(team_id: int = 66, limit: int = 2) -> list[NormalisedMatch]:
    if not FOOTBALL_API_KEY:
        return []

    url = f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY.strip()}
    matches = []

    # 1. Fetch the immediate next scheduled match
    upcoming_res = requests.get(url, headers=headers, params={"status": "SCHEDULED", "limit": 1})
    if upcoming_res.status_code == 200:
        scheduled = upcoming_res.json().get("matches", [])
        if scheduled:
            # Grab the very next match on the calendar
            matches.append(parse_football_match(scheduled[0]))

    # 2. Fetch the most recent finished match
    past_res = requests.get(url, headers=headers, params={"status": "FINISHED", "limit": 10})
    if past_res.status_code == 200:
        finished = past_res.json().get("matches", [])
        if finished:
            matches.append(parse_football_match(finished[-1]))

    return matches