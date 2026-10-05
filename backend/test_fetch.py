import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("PANDASCORE_API_KEY")

if not API_KEY:
    raise ValueError("Missing PANDASCORE_API_KEY. Check your .env file.")

def fetch_cs2_matches():
    # PandaScore endpoint for CS2 matches
    url = "https://api.pandascore.co/csgo/matches/upcoming"

    # Pass tolen explicitly a a query parameter
    params = {
        "token": API_KEY.strip(),
        "page[size]": 5
    }

    print("Calling PandaScore CS2 API...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Failed with status code {response.status_code}: {response.text}")
        return

    matches = response.json()
    print(f"\nFetched {len(matches)} upcoming CS2 matches\n")

    for match in matches:
        match_name = match.get("name", "Unknown Match")
        scheduled_at = match.get("scheduled_at", "TBD")
        tournament = match.get("league", {}).get("name", "Unknown League")

        # Extract team names
        opponents = [
            opp["opponent"]["name"]
            for opp in match.get("opponents", [])
            if opp.get("opponent")
        ]
        matchup = " vs ".join(opponents) if len(opponents) == 2 else match_name

        print(f"🏆 {tournament}")
        print(f"⚔️  {matchup}")
        print(f"🕒 Scheduled: {scheduled_at}")
        print("-" * 40)

if __name__ == "__main__":
    fetch_cs2_matches()