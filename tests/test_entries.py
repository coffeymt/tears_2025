import sys
import os
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.models.week import Week
from app.services.entries import create_entry, get_entries_for_user
from app.routes.entries import router
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta
from app.services.entries import update_entry, delete_entry
import json
import uuid


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text('DROP TABLE IF EXISTS entries'))
        except Exception:
            pass


def test_create_and_get_entry_service():
    db = SessionLocal()
    try:
        # create user and week
        user = User(email=f"{uuid.uuid4()}@example.com", hashed_password='x')
        db.add(user)
        week = Week(season_year=2025, week_number=1)
        db.add(week)
        db.commit()
        db.refresh(user)
        db.refresh(week)

        entry = create_entry(db, user.id, week.id, picks={'a': 1}, name='ServiceEntry')
        assert entry.id is not None

        got = get_entries_for_user(db, user.id)
        assert len(got) >= 1
        assert got[0].picks == {'a': 1}
    finally:
        db.close()


def test_entries_endpoints():
    client = TestClient(app)
    db = SessionLocal()
    try:
        # register through API to get token (use unique email)
        email = f"{uuid.uuid4()}@example.com"
        reg = client.post('/api/auth/register', json={'email': email, 'password': 'x'})
        assert reg.status_code == 200
        # login
        login = client.post('/api/auth/login', json={'email': email, 'password': 'x'})
        assert login.status_code == 200
        token = login.json()['access_token']

        user = db.query(User).filter(User.email == email).one()
        week = Week(season_year=2025, week_number=2)
        db.add(week)
        db.commit()
        db.refresh(user)
        db.refresh(week)

        payload = {'week_id': week.id, 'name': 'SvcEntry', 'picks': {'x': 2}}
        r = client.post('/api/entries', json=payload, headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 201
        data = r.json()
        assert 'id' in data

        r2 = client.get(f'/api/users/{user.id}/entries')
        assert r2.status_code == 200
        items = r2.json()
        assert any(item['week_id'] == week.id for item in items)
    finally:
        db.close()


def test_update_and_delete_endpoints_and_locking():
    client = TestClient(app)
    db = SessionLocal()
    try:
        # register and login user to get token (unique email)
        email2 = f"{uuid.uuid4()}@example.com"
        reg = client.post('/api/auth/register', json={'email': email2, 'password': 'x'})
        assert reg.status_code == 200
        login = client.post('/api/auth/login', json={'email': email2, 'password': 'x'})
        assert login.status_code == 200
        token = login.json()['access_token']

        week = Week(season_year=2025, week_number=3)
        db.add(week)
        db.commit()
        db.refresh(week)

        # create entry via API
        res = client.post('/api/entries', json={'week_id': week.id, 'name': 'EntryToUpdate', 'picks': {'a': 1}}, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 201
        entry_id = res.json()['id']

        # update entry successfully
        r = client.patch(f'/api/entries/{entry_id}', json={'picks': {'a': 2}}, headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200

        # set week lock_time to past to simulate locked week
        week.lock_time = datetime.utcnow() - timedelta(minutes=1)
        db.add(week)
        db.commit()

        # update should fail with 400 due to lock
        r2 = client.patch(f'/api/entries/{entry_id}', json={'picks': {'a': 3}}, headers={'Authorization': f'Bearer {token}'})
        assert r2.status_code == 400

        # delete should also fail due to lock
        r3 = client.delete(f'/api/entries/{entry_id}', headers={'Authorization': f'Bearer {token}'})
        assert r3.status_code == 400
    finally:
        db.close()


def test_duplicate_entry_name_create_and_rename_conflict():
    client = TestClient(app)
    db = SessionLocal()
    try:
        # register and login user to get token
        email = f"{uuid.uuid4()}@example.com"
        reg = client.post('/api/auth/register', json={'email': email, 'password': 'x'})
        assert reg.status_code == 200
        login = client.post('/api/auth/login', json={'email': email, 'password': 'x'})
        assert login.status_code == 200
        token = login.json()['access_token']

        # create a week
        week = Week(season_year=2025, week_number=4)
        db.add(week)
        db.commit()
        db.refresh(week)

        # create first entry with name 'Alpha'
        r1 = client.post('/api/entries', json={'week_id': week.id, 'name': 'Alpha', 'picks': {'a':1}}, headers={'Authorization': f'Bearer {token}'})
        assert r1.status_code == 201

        # attempt to create another entry for same user/same season with same name -> 409
        r2 = client.post('/api/entries', json={'week_id': week.id, 'name': 'Alpha', 'picks': {'b':2}}, headers={'Authorization': f'Bearer {token}'})
        assert r2.status_code == 409

        # create a second week for same season and a second entry with different name
        week2 = Week(season_year=2025, week_number=5)
        db.add(week2)
        db.commit()
        db.refresh(week2)
        r3 = client.post('/api/entries', json={'week_id': week2.id, 'name': 'Beta', 'picks': {'c':3}}, headers={'Authorization': f'Bearer {token}'})
        assert r3.status_code == 201
        entry2_id = r3.json()['id']

        # attempt to rename entry2 to 'Alpha' -> should conflict
        r4 = client.patch(f'/api/entries/{entry2_id}', json={'name': 'Alpha'}, headers={'Authorization': f'Bearer {token}'})
        assert r4.status_code == 409
    finally:
        db.close()
