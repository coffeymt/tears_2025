import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from fastapi.testclient import TestClient
from app.db import SessionLocal, engine
from app.models.base import Base
from app.models.week import Week
from app.models.team import Team
import uuid
from datetime import datetime, timedelta


client = TestClient(app)


def register_and_auth():
    email = f"endpoint+{uuid.uuid4()}@test.com"
    password = "pass123"
    # register
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    # login
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_post_pick_locked_week_returns_403():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # create a locked week and a team
    week = Week(season_year=2025, week_number=99, lock_time=datetime.utcnow() - timedelta(hours=1))
    db.add(week)
    team = Team(abbreviation=f"LCK{uuid.uuid4().hex[:6]}", name="Locked Team", city="Lock")
    db.add(team)
    db.commit()
    db.refresh(week)
    db.refresh(team)

    headers = register_and_auth()

    # create entry via API
    r = client.post("/api/entries", json={"week_id": week.id, "name": "E1", "picks": {}}, headers=headers)
    assert r.status_code == 201
    entry_id = r.json()["id"]

    # try to submit pick - should be forbidden (403)
    r = client.post("/api/picks", json={"entry_id": entry_id, "week_id": week.id, "team_id": team.id}, headers=headers)
    assert r.status_code == 403


def test_post_pick_unlocked_week_returns_201():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # create an unlocked week and a team
    week = Week(season_year=2025, week_number=100, lock_time=datetime.utcnow() + timedelta(hours=2))
    db.add(week)
    team = Team(abbreviation=f"ULK{uuid.uuid4().hex[:6]}", name="Unlocked Team", city="Nowhere")
    db.add(team)
    db.commit()
    db.refresh(week)
    db.refresh(team)

    headers = register_and_auth()

    # create entry via API
    r = client.post("/api/entries", json={"week_id": week.id, "name": "E2", "picks": {}}, headers=headers)
    assert r.status_code == 201
    entry_id = r.json()["id"]

    # submit pick - should succeed
    r = client.post("/api/picks", json={"entry_id": entry_id, "week_id": week.id, "team_id": team.id}, headers=headers)
    assert r.status_code == 201
