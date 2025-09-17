import sys
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from fastapi.testclient import TestClient
from app.models.base import Base
from app.db import engine, SessionLocal
from app.models.week import Week
from app.models.game import Game
from app.models.team import Team
from app.models.pick import Pick


client = TestClient(app)


def setup_db():
    Base.metadata.create_all(bind=engine)


def teardown_db():
    Base.metadata.drop_all(bind=engine)


def test_reveal_snapshot_before_and_after_lock():
    setup_db()
    db = SessionLocal()
    try:
        # create week that locks in 1 minute
        week = Week(season_year=2025, week_number=1, lock_time=datetime.now(timezone.utc) + timedelta(minutes=1))
        db.add(week)
        db.commit()
        db.refresh(week)

        # create teams
        t1 = Team(abbreviation="T1", name="Team 1")
        t2 = Team(abbreviation="T2", name="Team 2")
        db.add_all([t1, t2])
        db.commit()
        db.refresh(t1)
        db.refresh(t2)

        # create a game (Game model stores team abbrs)
        g = Game(week_id=week.id, start_time=datetime.now(timezone.utc), home_team_abbr=t1.abbreviation, away_team_abbr=t2.abbreviation, status="scheduled")
        db.add(g)
        db.commit()
        db.refresh(g)

        # create two picks for the game
        p1 = Pick(entry_id=1, week_id=week.id, team_id=t1.id)
        p2 = Pick(entry_id=2, week_id=week.id, team_id=t2.id)
        db.add_all([p1, p2])
        db.commit()

        # Before lock: reveal-snapshot should return exists True and locked False
        resp = client.get(f"/api/public/weeks/{week.id}/reveal-snapshot")
        assert resp.status_code == 200
        j = resp.json()
        assert j.get("exists") is True
        assert j.get("locked") is False

        # Fast-forward lock_time by updating week.lock_time to past
        week.lock_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.add(week)
        db.commit()

        # Update game as final with scores so winner is determinable
        g.home_score = 24
        g.away_score = 17
        g.status = "final"
        db.add(g)
        db.commit()

        # Now snapshot should be locked and show aggregated pick_counts and winning_team_id
        resp2 = client.get(f"/api/public/weeks/{week.id}/reveal-snapshot")
        assert resp2.status_code == 200
        j2 = resp2.json()
        assert j2.get("exists") is True
        assert j2.get("locked") is True
        games = j2.get("games")
        assert isinstance(games, list) and len(games) >= 1
        game_info = next((x for x in games if x["id"] == g.id), None)
        assert game_info is not None
        assert game_info.get("winning_team_id") == t1.id
        # pick_counts should show picks per team id
        pick_counts = game_info.get("pick_counts")
        assert isinstance(pick_counts, dict)
        keys = set(map(lambda x: int(x) if isinstance(x, str) and x.isdigit() else x, pick_counts.keys()))
        assert t1.id in keys

    finally:
        db.close()
        teardown_db()


def test_reveal_snapshot_nonexistent_week():
    setup_db()
    try:
        resp = client.get("/api/public/weeks/99999/reveal-snapshot")
        assert resp.status_code == 200
        j = resp.json()
        assert j.get("exists") is False
    finally:
        teardown_db()
