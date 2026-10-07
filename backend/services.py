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