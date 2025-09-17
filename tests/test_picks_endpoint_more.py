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


def register_and_auth(email_prefix: str = "more"):
    email = f"{email_prefix}+{uuid.uuid4()}@test.com"
    password = "pass123"
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_post_duplicate_pick_returns_409():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    week = Week(season_year=2025, week_number=301, lock_time=datetime.utcnow() + timedelta(hours=2))
    db.add(week)
    team = Team(abbreviation=f"DUP{uuid.uuid4().hex[:6]}", name="Dup Team", city="D")
    db.add(team)
    db.commit()
    db.refresh(week)
    db.refresh(team)

    headers = register_and_auth("dup")

    r = client.post("/api/entries", json={"week_id": week.id, "name": "DupEntry", "picks": {}}, headers=headers)
    assert r.status_code == 201
    entry_id = r.json()["id"]

    r = client.post("/api/picks", json={"entry_id": entry_id, "week_id": week.id, "team_id": team.id}, headers=headers)
    assert r.status_code == 201

    # duplicate POST should be conflict
    r = client.post("/api/picks", json={"entry_id": entry_id, "week_id": week.id, "team_id": team.id}, headers=headers)
    assert r.status_code == 409


def test_post_pick_wrong_user_returns_400():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    week = Week(season_year=2025, week_number=302, lock_time=datetime.utcnow() + timedelta(hours=2))
    db.add(week)
    team = Team(abbreviation=f"OWN{uuid.uuid4().hex[:6]}", name="Owner Team", city="O")
    db.add(team)
    db.commit()
    db.refresh(week)
    db.refresh(team)

    # register user A and create entry
    headers_a = register_and_auth("ownerA")
    r = client.post("/api/entries", json={"week_id": week.id, "name": "OwnerEntry", "picks": {}}, headers=headers_a)
    assert r.status_code == 201
    entry_id = r.json()["id"]

    # register user B and attempt to post using A's entry -> should be 400 (not authorized)
    headers_b = register_and_auth("ownerB")
    r = client.post("/api/picks", json={"entry_id": entry_id, "week_id": week.id, "team_id": team.id}, headers=headers_b)
    assert r.status_code == 400
