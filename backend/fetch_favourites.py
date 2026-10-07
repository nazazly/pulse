import os 
from datetime import datetime
from pathlib import Path
import zoneinfo
import requests
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("PANDASCORE_API_KEY")
BASE_URL = "https://api.pandascore.co"

if not API_KEY:
    raise ValueError("Missing PANDASCORE_API_KEY in .env")

SGT_TZ = zoneinfo.ZoneInfo("Asia/Singapore")

def format_to_sgt(utc_iso_string: str) -> str:
    """
    Converts a raw ISO UTC string to a readable Singapore time format
    """
    if not utc_iso_string:
        return "TBD"
    # Parse UTC ISO string
    utc_dt = datetime.fromisoformat(utc_iso_string.replace("Z", "+00:00"))
    sgt_dt = utc_dt.astimezone(SGT_TZ)
    # Output: '05 Oct 2025, 19:30 SGT'
    return sgt_dt.strftime("%d %b %Y, %H:%M SGT")

def get_team_id_by_name(videogame_slug: str, team_name: str) -> dict:
    """
    Search endpoint logic:
    Allows user to type any team name and retrieves their exact ID and slug.
    """
    url = f"{BASE_URL}/{videogame_slug}/teams"
    params = {
        "token": API_KEY.strip(),
        "search[name]": team_name,
        "page[size]": 1
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json():
        t = response.json()[0]
        return {
            "id": t["id"],
            "name": t["name"],
            "slug": t["slug"],
            "acronym": t.get("acronym") or t["name"],
        }
    return None

def fetch_team_fixtures_and_results(team_id: int, page_size: int = 3):
    """
    Fetches both upcoming and finished matches for a given team ID.
    """
    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {
        "token": API_KEY.strip(),
        "sort": "-scheduled_at", # Most recent first
        "page[size]": page_size,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching matches for team ID {team_id}: {response.text}")
        return[]
    return response.json()

def parse_match_card(match: dict, target_team_id: int):
    """
    Normalises a raw PandaScore match into a clean match card
    with scores, status, and Singapore time
    """
    name = match.get("name", "Unknown Match")
    status = match.get("status", "unknown").upper()
    scheduled_sgt = format_to_sgt(match.get("scheduled_at"))

    # Extract score details
    results = match.get("results", [])
    scores = []
    winner_id = match.get("winner_id")

    for r in results:
        team_id = r.get("team_id")
        score = r.get("score")
        scores.append(f"{score}")

    score_display = " - ".join(scores) if scores else "vs"

    # Determine Win / Loss for target team if finished
    result_tag = ""
    if status == "FINISHED":
        if winner_id == target_team_id:
            result_tag = "🟢 [WIN]"
        elif winner_id is not None:
            result_tag = "🔴 [LOSS]"
        else:
            result_tag = "⚪ [DRAW]"

    return {
        "title": name,
        "status": status,
        "time_sgt": scheduled_sgt,
        "score": score_display,
        "result_tag": result_tag
    }

def display_team_hub(videogame_slug: str, team_query: str):
    """
    Simulates what the dashboard feed does for a favourited team.
    """
    team = get_team_id_by_name(videogame_slug, team_query)
    if not team:
        print(f"❌ Team '{team_query}' not found.")
        return

    print(
        f"\n========================================================"
    )
    print(f"⭐ FAVORITE: {team['name']} ({videogame_slug.upper()}) | ID: {team['id']}")
    print(
        f"========================================================"
    )

    matches = fetch_team_fixtures_and_results(team["id"], page_size=4)

    for m in matches:
        card = parse_match_card(m, team["id"])
        print(f"[{card['status']}] {card['result_tag']}")
        print(f"⚔️  {card['title']}")
        print(f"📊 Score: {card['score']}")
        print(f"🕒 Time:  {card['time_sgt']}")
        print("-" * 50)

def main():
    # Demonstrating dynamic team search and match formatting
    # Users can favourite ANY team: NAVI, PRX, Cloud9, G2, etc
    display_team_hub("csgo", "Natus Vincere")
    display_team_hub("valorant", "Paper Rex")

if __name__ == "__main__":
    main()