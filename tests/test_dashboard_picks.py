import sys
import os
from datetime import datetime, timezone, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import engine, SessionLocal
from app.models.base import Base
from app.models.entry import Entry
from app.models.week import Week
from app.models.pick import Pick
from app.models.team import Team
from app.services.dashboard import get_picks_for_entries
from app.main import app


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_get_picks_for_entries_mapping():
    db = SessionLocal()
    try:
        # create week, teams, entries, and picks
        w = Week(season_year=2025, week_number=1, is_current=True, lock_time=datetime.now(timezone.utc) + timedelta(hours=1))
        db.add(w)
        db.commit()
        db.refresh(w)

        t1 = Team(abbreviation="T1", name="Team One")
        t2 = Team(abbreviation="T2", name="Team Two")
        db.add_all([t1, t2])
        db.commit()
        db.refresh(t1)
        db.refresh(t2)

        e1 = Entry(user_id=1, week_id=w.id, name="E1", season_year=2025, picks=[], is_eliminated=False)
        e2 = Entry(user_id=1, week_id=w.id, name="E2", season_year=2025, picks=[], is_eliminated=False)
        e3 = Entry(user_id=2, week_id=w.id, name="E3", season_year=2025, picks=[], is_eliminated=False)
        db.add_all([e1, e2, e3])
        db.commit()
        db.refresh(e1)
        db.refresh(e2)
        db.refresh(e3)

        # create picks for e1 and e3 only
        p1 = Pick(entry_id=e1.id, week_id=w.id, team_id=t1.id)
        p3 = Pick(entry_id=e3.id, week_id=w.id, team_id=t2.id)
        db.add_all([p1, p3])
        db.commit()

        entry_ids = [e1.id, e2.id, e3.id]
        mapping = get_picks_for_entries(db, entry_ids, w.id)

        assert isinstance(mapping, dict)
        assert mapping[e1.id]["team_id"] == t1.id
        assert mapping[e1.id]["team_abbr"] == "T1"
        assert mapping[e2.id] is None
        assert mapping[e3.id]["team_id"] == t2.id

        # empty entry list should return empty mapping
        empty_map = get_picks_for_entries(db, [], w.id)
        assert empty_map == {}

    finally:
        db.close()
