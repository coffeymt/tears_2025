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
from app.services.dashboard import get_entries_for_user, get_current_week_info
from app.main import app


def setup_module(module):
    # create tables in test DB
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_get_entries_for_user_and_week_info():
    db = SessionLocal()
    try:
        # create a week and entry
        w = Week(season_year=2025, week_number=1, is_current=True, lock_time=datetime.now(timezone.utc) + timedelta(hours=1))
        db.add(w)
        db.commit()
        db.refresh(w)
        e = Entry(user_id=42, week_id=w.id, name="Test Entry", season_year=2025, picks=[], is_eliminated=False)
        db.add(e)
        db.commit()

        entries = get_entries_for_user(db, 42)
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert entries[0]["name"] == "Test Entry"

        week_info = get_current_week_info(db)
        assert week_info is not None
        assert week_info["week_number"] == 1
        assert "countdown_seconds" in week_info
    finally:
        db.close()
