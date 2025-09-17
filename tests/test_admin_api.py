import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.db import engine, SessionLocal
from app.models.base import Base
from app.utils.security import create_access_token
from app.models.user import User
from app.models.entry import Entry
import datetime as _dt


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_admin_user_and_entry_endpoints():
    client = TestClient(app)
    # create an admin user and a regular user
    db = SessionLocal()
    try:
        admin = User(email="admin@example.com", hashed_password="x", is_admin=True)
        user = User(email="user@example.com", hashed_password="x", is_admin=False)
        db.add(admin)
        db.add(user)
        db.commit()
        db.refresh(admin)
        db.refresh(user)
        # create an entry for the regular user
        entry = Entry(user_id=user.id, week_id=1, name="E1", season_year=2025, picks={}, is_eliminated=False)
        db.add(entry)
        db.commit()
        db.refresh(entry)
    finally:
        # capture ids before closing session to avoid DetachedInstanceError
        admin_id = int(admin.id)
        user_id = int(user.id)
        db.close()

    from app.utils.security import create_access_token as _create_token
    admin_token = _create_token(str(admin_id))
    user_token = _create_token(str(user_id))

    # admin can list users
    r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    users = r.json()
    assert any(u["email"] == "user@example.com" for u in users)

    # regular user forbidden
    r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code in (401, 403)

    # admin can patch user to disable
    r = client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    # admin can list entries
    r = client.get("/api/admin/entries", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    entries = r.json()
    assert any(e["id"] == entry.id for e in entries)

    # admin can mark entry eliminated
    r = client.patch(f"/api/admin/entries/{entry.id}/elimination", json={"is_eliminated": True}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["is_eliminated"] is True

    # admin can mark entry as paid and it's persisted
    r = client.patch(f"/api/admin/entries/{entry.id}/payment", json={"is_paid": True}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["is_paid"] is True

    # verify persisted in DB
    db = SessionLocal()
    try:
        from app.models.entry import Entry as EntryModel
        e = db.get(EntryModel, entry.id)
        assert e.is_paid is True
    finally:
        db.close()
