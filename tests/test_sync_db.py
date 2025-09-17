import sys
import os
import pytest
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import SessionLocal, engine
from app.models.week import Week
from app.models.game import Game
from app.services.sync import transform_and_sync_games


def setup_module(module):
    # Ensure tables exist for tests using SQLAlchemy metadata (simple, uses sqlite dev.db)
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    # Drop games table to keep sqlite clean for repeated runs
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text('DROP TABLE IF EXISTS games'))
        except Exception:
            pass


def test_transform_and_sync_creates_games():
    db = SessionLocal()
    try:
        # ensure a week exists
        week = Week(season_year=2025, week_number=1, is_current=False)
        db.add(week)
        db.commit()
        db.refresh(week)

        # build a minimal raw payload compatible with transformer tests
        raw = {"events": [
            {
                "date": "2025-09-14T20:15:00Z",
                "status": {"type": {"state": "pre"}},
                "competitions": [{"competitors": [
                    {"homeAway": "away", "team": {"abbreviation": "MIA"}, "score": 7},
                    {"homeAway": "home", "team": {"abbreviation": "NE"}, "score": 10}
                ]}]
            }
        ]}

        res = transform_and_sync_games(raw, year=2025, week=1, db=db)
        assert isinstance(res, dict)
        assert res.get("created") == 1
        # verify DB has a game
        g = db.query(Game).filter(Game.week_id == week.id).one_or_none()
        assert g is not None
        assert g.home_team_abbr == "NE"
        assert g.away_team_abbr == "MIA"
    finally:
        db.close()
