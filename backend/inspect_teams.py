import os
from pathlib import Path
import requests
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("PANDASCORE_API_KEY")

def inspect_team(videogame_slug, search_query):
    url = f"https://api.pandascore.co/{videogame_slug}/teams"
    params = {
        "token": API_KEY.strip(),
        "search[name]": search_query,
        "page[size]": 3
    }
    res = requests.get(url, params=params)
    print(f"\n=== Searching '{search_query}' in {videogame_slug} ===")
    if res.status_code != 200:
        print(f"Error {res.status_code}: {res.text}")
        return
    
    teams = res.json()
    for t in teams:
        print(f"ID: {t.get('id')} | Name: {t.get('name')} | Slug: {t.get('slug')}")
        
        # Check their last 2 matches to verify this is the active roster
        matches_url = f"https://api.pandascore.co/teams/{t.get('id')}/matches"
        m_res = requests.get(matches_url, params={"token": API_KEY.strip(), "page[size]": 2, "sort": "-scheduled_at"})
        if m_res.status_code == 200 and m_res.json():
            print("  Recent matches found:")
            for m in m_res.json():
                print(f"   • [{m.get('status')}] {m.get('name')} ({m.get('scheduled_at')})")
        else:
            print("  No recent matches on this ID.")

if __name__ == "__main__":
    inspect_team("csgo", "Natus Vincere")
    inspect_team("valorant", "Paper Rex")