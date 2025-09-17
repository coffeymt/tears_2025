import sys
import os
import pytest

# Ensure project root is on sys.path so `import app` works when pytest runs this file directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.sync import transform_espn_response


def make_event(home_abbr, away_abbr, home_score=None, away_score=None, date="2025-09-14T20:15:00Z", state="pre"):
    return {
        "date": date,
        "status": {"type": {"state": state}},
        "competitions": [
            {
                "competitors": [
                    {"homeAway": "away", "team": {"abbreviation": away_abbr}, "score": away_score},
                    {"homeAway": "home", "team": {"abbreviation": home_abbr}, "score": home_score},
                ]
            }
        ],
    }


def test_transform_happy_path():
    raw = {"events": [make_event("NE", "MIA", home_score=10, away_score=7)]}
    games = transform_espn_response(raw)
    assert isinstance(games, list)
    assert len(games) == 1
    g = games[0]
    assert g["home_team_abbr"] == "NE"
    assert g["away_team_abbr"] == "MIA"
    assert g["status"] == "scheduled"
    assert g["home_score"] == 10
    assert g["away_score"] == 7


def test_transform_skips_malformed():
    # event missing competitors
    raw = {"events": [{"date": "2025-09-14T20:15:00Z"}, make_event("JAX", "NYG")]}
    games = transform_espn_response(raw)
    assert len(games) == 1
    assert games[0]["home_team_abbr"] == "JAX"