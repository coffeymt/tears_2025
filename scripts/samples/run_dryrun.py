import json
import pathlib
from scripts import import_from_gcs as ig

p = pathlib.Path(__file__).parent
for fname in ['teams.json','users.json','weeks.json','games.json','entries.json','picks.json']:
    path = p / fname
    text = path.read_text()
    data = json.loads(text)
    if fname.startswith('teams'):
        res = ig.process_teams(data, dry_run=True)
    elif fname.startswith('users'):
        res = ig.process_users(data, dry_run=True)
    elif fname.startswith('weeks'):
        res = ig.process_weeks(data, dry_run=True)
    elif fname.startswith('games'):
        res = ig.process_games(data, dry_run=True)
    elif fname.startswith('entries'):
        res = ig.process_entries(data, dry_run=True)
    elif fname.startswith('picks'):
        res = ig.process_picks(data, dry_run=True)
    else:
        res = {'skipped': True}
    print(f"{fname} -> {res}")
