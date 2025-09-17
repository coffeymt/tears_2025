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
    email = f"patch+{uuid.uuid4()}@test.com"
    password = "pass123"
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_patch_pick_update_and_lock_behavior():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # create unlocked week and two teams
    week = Week(season_year=2025, week_number=201, lock_time=datetime.utcnow() + timedelta(hours=2))
    db.add(week)
    team1 = Team(abbreviation=f"P1{uuid.uuid4().hex[:6]}", name="Patch Team 1", city="C1")
    team2 = Team(abbreviation=f"P2{uuid.uuid4().hex[:6]}", name="Patch Team 2", city="C2")
    db.add(team1)
    db.add(team2)
    db.commit()
    db.refresh(week)
    db.refresh(team1)
    db.refresh(team2)

    headers = register_and_auth()

    # create entry
    r = client.post("/api/entries", json={"week_id": week.id, "name": "PatchEntry", "picks": {}}, headers=headers)
    assert r.status_code == 201
    entry_id = r.json()["id"]

    # submit initial pick for team1
    r = client.post("/api/picks", json={"entry_id": entry_id, "week_id": week.id, "team_id": team1.id}, headers=headers)
    assert r.status_code == 201
    pick_id = r.json()["id"]

    # update pick to team2 (allowed before lock)
    r = client.patch(f"/api/picks/{pick_id}", json={"team_id": team2.id}, headers=headers)
    assert r.status_code == 200

    # create another week in same season and an entry that uses team1 (to cause a duplicate-team conflict on update)
    week2 = Week(season_year=2025, week_number=202, lock_time=datetime.utcnow() + timedelta(hours=2))
    db.add(week2)
    db.commit()
    db.refresh(week2)

    r = client.post("/api/entries", json={"week_id": week2.id, "name": "OtherEntry", "picks": {}}, headers=headers)
    assert r.status_code == 201
    other_entry_id = r.json()["id"]
    r = client.post("/api/picks", json={"entry_id": other_entry_id, "week_id": week2.id, "team_id": team1.id}, headers=headers)
    assert r.status_code == 201

    # try updating our original pick back to team1 -> should raise 409 (already picked this season by the other entry)
    r = client.patch(f"/api/picks/{pick_id}", json={"team_id": team1.id}, headers=headers)
    assert r.status_code == 409

    # lock the week by updating lock_time to past
    db.query(Week).filter(Week.id == week.id).update({"lock_time": datetime.utcnow() - timedelta(hours=1)})
    db.commit()

    # attempt to update after lock -> 403
    r = client.patch(f"/api/picks/{pick_id}", json={"team_id": team2.id}, headers=headers)
    assert r.status_code == 403
