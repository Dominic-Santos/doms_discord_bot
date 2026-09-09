from datetime import datetime
import json

# Load tournament data
with open('data/tournaments.json', 'r') as f:
    data = json.load(f)

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
