import json
import pathlib
from scripts import import_from_gcs as ig

SAMPLES = pathlib.Path("scripts/samples")


def load(name):
    return json.loads((SAMPLES / name).read_text())


def test_process_teams_users_weeks_games_entries_picks_dryrun():
    teams = load("teams.json")
    users = load("users.json")
    weeks = load("weeks.json")
    games = load("games.json")
    entries = load("entries.json")
    picks = load("picks.json")

    t_res = ig.process_teams(teams, dry_run=True)
    u_res = ig.process_users(users, dry_run=True)
    w_res = ig.process_weeks(weeks, dry_run=True)
    g_res = ig.process_games(games, dry_run=True)
    e_res = ig.process_entries(entries, dry_run=True)
    p_res = ig.process_picks(picks, dry_run=True)

    assert t_res["created"] == 2
    assert u_res["created"] == 2
    assert w_res["created"] == 2
    assert g_res["created"] == 2
    assert e_res["created"] == 2
    assert p_res["created"] == 2
