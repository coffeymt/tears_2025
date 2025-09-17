import sys
import os
from datetime import datetime, timezone, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.db import engine, SessionLocal
from app.models.base import Base
from app.models.user import User
from app.models.week import Week
from app.models.entry import Entry
from app.models.team import Team
from app.models.pick import Pick
from app.utils import security

client = TestClient(app)


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def create_user_and_token(db, email="user@example.com"):
    u = User(email=email, hashed_password=security.get_password_hash("pass"))
    db.add(u)
    db.commit()
    db.refresh(u)
    token = security.create_access_token(subject=str(u.id))
    return u, token


def test_dashboard_endpoint_returns_entries_and_picks():
    db = SessionLocal()
    try:
        # create user and token
        user, token = create_user_and_token(db)

        # create week
        w = Week(season_year=2025, week_number=1, is_current=True, lock_time=datetime.now(timezone.utc) + timedelta(hours=1))
        db.add(w)
        db.commit()
        db.refresh(w)

        # create team and entry and pick
        t = Team(abbreviation="T1", name="Team One")
        db.add(t)
        db.commit()
        db.refresh(t)

        e = Entry(user_id=user.id, week_id=w.id, name="E1", season_year=2025, picks=[], is_eliminated=False)
        db.add(e)
        db.commit()
        db.refresh(e)

        p = Pick(entry_id=e.id, week_id=w.id, team_id=t.id)
        db.add(p)
        db.commit()

        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/dashboard", headers=headers)
        assert res.status_code == 200
        j = res.json()
        assert j["user_id"] == user.id
        assert len(j["entries"]) == 1
        assert j["entries"][0]["current_pick"]["team_id"] == t.id
    finally:
        db.close()


def test_dashboard_endpoint_requires_auth():
    # No Authorization header should return 401
    res = client.get("/api/dashboard")
    # Depending on HTTPBearer behavior we may get 401 or 403; accept either
    assert res.status_code in (401, 403)


def test_dashboard_endpoint_shows_eliminated_entry():
    db = SessionLocal()
    try:
        user, token = create_user_and_token(db, email="elim@example.com")
        w = Week(season_year=2025, week_number=1, is_current=True, lock_time=datetime.now(timezone.utc) + timedelta(hours=1))
        db.add(w)
        db.commit()
        db.refresh(w)

        e = Entry(user_id=user.id, week_id=w.id, name="ElimEntry", season_year=2025, picks=[], is_eliminated=True)
        db.add(e)
        db.commit()
        db.refresh(e)

        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/dashboard", headers=headers)
        assert res.status_code == 200
        j = res.json()
        assert len(j["entries"]) == 1
        assert j["entries"][0]["is_eliminated"] is True
    finally:
        db.close()
