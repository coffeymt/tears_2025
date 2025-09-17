import sys
import os
import pytest
import sys
import os
import pytest
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import SessionLocal, engine
from app.models.base import Base
from app.models.week import Week
from app.models.game import Game
from app.services.sync import transform_and_sync_games


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    # Clean up games table
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text('DROP TABLE IF EXISTS games'))
        except Exception:
            pass


def test_rollback_on_failure(monkeypatch):
    db = SessionLocal()
    try:
        # create week
        week = Week(season_year=2025, week_number=99, is_current=False)
        db.add(week)
        db.commit()
        db.refresh(week)

        # seed existing game so we can observe rollback restores it
        existing = Game(week_id=week.id, start_time=datetime.now(timezone.utc), home_team_abbr="AAA", away_team_abbr="BBB", status="scheduled")
        db.add(existing)
        db.commit()

        # prepare payload with two events so insert will attempt two adds
        raw = {"events": [
            {"date": "2025-09-14T20:15:00Z", "status": {"type": {"state": "pre"}}, "competitions": [{"competitors": [{"homeAway": "away", "team": {"abbreviation": "MIA"}, "score": 7}, {"homeAway": "home", "team": {"abbreviation": "NE"}, "score": 10}]}]},
            {"date": "2025-09-15T20:15:00Z", "status": {"type": {"state": "pre"}}, "competitions": [{"competitors": [{"homeAway": "away", "team": {"abbreviation": "DAL"}, "score": 3}, {"homeAway": "home", "team": {"abbreviation": "NYG"}, "score": 6}]}]}
        ]}

        # monkeypatch db.add to raise on second add to simulate failure during insert
        original_add = db.add
        state = {"calls": 0}

        def fake_add(obj):
            state["calls"] += 1
            if state["calls"] >= 2:
                raise RuntimeError("simulated insert failure")
            return original_add(obj)

        db.add = fake_add

        with pytest.raises(RuntimeError):
            transform_and_sync_games(raw, year=2025, week=99, db=db)

        # After the failed sync, original game should still exist (rolled back)
        db2 = SessionLocal()
        try:
            g = db2.query(Game).filter(Game.week_id == week.id).all()
            assert any(x.home_team_abbr == "AAA" and x.away_team_abbr == "BBB" for x in g)
        finally:
            db2.close()

    finally:
        db.close()


def test_double_sync_overwrites():
    db = SessionLocal()
    try:
        week = Week(season_year=2025, week_number=100, is_current=False)
        db.add(week)
        db.commit()
        db.refresh(week)

        raw1 = {"events": [
            {"date": "2025-09-14T20:15:00Z", "status": {"type": {"state": "pre"}}, "competitions": [{"competitors": [{"homeAway": "away", "team": {"abbreviation": "MIA"}}, {"homeAway": "home", "team": {"abbreviation": "NE"}}]}]}
        ]}

        raw2 = {"events": [
            {"date": "2025-09-16T20:15:00Z", "status": {"type": {"state": "pre"}}, "competitions": [{"competitors": [{"homeAway": "away", "team": {"abbreviation": "PHI"}}, {"homeAway": "home", "team": {"abbreviation": "DAL"}}]}]}
        ]}

        res1 = transform_and_sync_games(raw1, year=2025, week=100, db=db)
        assert res1.get("created") == 1

        res2 = transform_and_sync_games(raw2, year=2025, week=100, db=db)
        assert res2.get("created") == 1

        # Final DB should reflect only raw2
        g = db.query(Game).filter(Game.week_id == week.id).all()
        assert len(g) == 1
        assert g[0].home_team_abbr == "DAL"
        assert g[0].away_team_abbr == "PHI"

    finally:
        db.close()
