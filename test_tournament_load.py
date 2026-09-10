from datetime import datetime
import json
from pathlib import Path

# Load tournament data
tournaments_file = Path("data/tournaments.json")
if tournaments_file.exists():
    with tournaments_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
else:
    print("No tournament data found; skipping tournament inspection.")
    data = {"tournaments": {}}

tournaments = data.get('tournaments', {})
print(f"Loaded tournaments: {list(tournaments.keys())}")

now = datetime.now()
print(f"Current time: {now}")

for tournament_id, tournament_data in tournaments.items():
    expires_at = tournament_data.get('expires_at')
    print(f"\nTournament: {tournament_id}")
    print(f"  Name: {tournament_data.get('name')}")
    print(f"  Expires at: {expires_at}")
    
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at)
            is_open = now <= exp_dt
            print(f"  Parsed datetime: {exp_dt}")
            print(f"  Is open: {is_open}")
        except ValueError as e:
            print(f"  Parse error: {e}")
