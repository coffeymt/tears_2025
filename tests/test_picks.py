import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import SessionLocal, engine
from app.main import app
from fastapi.testclient import TestClient
from app.services.entries import create_entry
import uuid
from app.models.week import Week
from app.models.entry import Entry
from app.models.user import User
from app.models.team import Team
from app.models.base import Base
from app.db import engine
from datetime import datetime, timedelta


client = TestClient(app)


def setup_user_and_week(db):
    user = User(email=f'pick+{uuid.uuid4()}@test.com', hashed_password='x')
    db.add(user)
    db.commit()
    db.refresh(user)

    week = Week(season_year=2025, week_number=1, lock_time=datetime.utcnow() + timedelta(hours=1))
    db.add(week)
    db.commit()
    db.refresh(week)

    return user, week


def test_create_pick_and_ownership(tmp_path, monkeypatch):
    db = SessionLocal()

    # ensure tables exist in test DB
    Base.metadata.create_all(bind=engine)

    # create user, week, and team
    user, week = setup_user_and_week(db)
    team = Team(abbreviation=f"TST{uuid.uuid4().hex[:6]}", name='Test Team', city='Test')
    db.add(team)
    db.commit()
    db.refresh(team)

    # create entry for user
    entry = create_entry(db, user.id, week.id, picks={}, name='Entry1')

    # simulate authenticated client by bypassing auth dependency in route calls is complex here;
    # instead call service directly to verify core logic
    from app.services.picks import create_pick, PickConflict

    # happy path
    p = create_pick(db, user.id, entry.id, week.id, team.id)
    assert p.id is not None

    # duplicate pick for same entry/week should raise conflict
    try:
        create_pick(db, user.id, entry.id, week.id, team.id)
        assert False, "Expected PickConflict"
    except PickConflict:
        pass


def test_pick_lock_behavior(tmp_path):
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # create user, week (locked), team, entry
    user = User(email=f'lock+{uuid.uuid4()}@test.com', hashed_password='x')
    db.add(user)
    week = Week(season_year=2025, week_number=9, lock_time=datetime.utcnow() - timedelta(hours=1))
    db.add(week)
    team = Team(abbreviation=f"LCK{uuid.uuid4().hex[:6]}", name='Locked Team', city='Lock')
    db.add(team)
    db.commit()
    db.refresh(user)
    db.refresh(week)
    db.refresh(team)

    entry = create_entry(db, user.id, week.id, picks={}, name='LockedEntry')

    from app.services.picks import create_pick, WeekLockedError

    try:
        create_pick(db, user.id, entry.id, week.id, team.id)
        assert False, "Expected WeekLockedError"
    except WeekLockedError:
        pass
