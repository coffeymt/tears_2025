import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.db import engine, SessionLocal
from app.models.base import Base
from app.models.user import User
from app.models.entry import Entry
from app.utils.security import create_access_token

import app.utils.email as email_utils


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_broadcast_filters(monkeypatch):
    client = TestClient(app)
    db = SessionLocal()
    try:
        admin = User(email="admin@example.com", hashed_password="x", is_admin=True)
        u1 = User(email="a@example.com", hashed_password="x", is_admin=False, is_active=True)
        u2 = User(email="b@example.com", hashed_password="x", is_admin=False, is_active=False)
        u3 = User(email="c@example.com", hashed_password="x", is_admin=False, is_active=True)
        db.add_all([admin, u1, u2, u3])
        db.commit()
        db.refresh(admin)
        db.refresh(u1)
        db.refresh(u2)
        db.refresh(u3)

        # u1 has a paid entry, u3 has an unpaid entry
        e1 = Entry(user_id=u1.id, week_id=1, name="E1", season_year=2025, picks={}, is_paid=True)
        e2 = Entry(user_id=u3.id, week_id=1, name="E2", season_year=2025, picks={}, is_paid=False)
        db.add_all([e1, e2])
        db.commit()
    finally:
        admin_id = int(admin.id)
        db.close()

    admin_token = create_access_token(str(admin_id))

    sent = []

    def fake_send_email(to, subject, body):
        sent.append(to)

    monkeypatch.setattr(email_utils, "send_email", fake_send_email)

    # filter=all -> should send to all users with emails (admin + u1 + u2 + u3)
    r = client.post("/api/admin/broadcast", json={"subject": "S", "body": "B", "filter": "all"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert set(r.json()["recipients"]) == set(["admin@example.com", "a@example.com", "b@example.com", "c@example.com"])

    sent.clear()
    # filter=active -> admin, u1, u3
    r = client.post("/api/admin/broadcast", json={"subject": "S", "body": "B", "filter": "active"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert set(r.json()["recipients"]) == set(["admin@example.com", "a@example.com", "c@example.com"])

    sent.clear()
    # filter=unpaid (any): users with at least one unpaid entry -> u3
    r = client.post("/api/admin/broadcast", json={"subject": "S", "body": "B", "filter": "unpaid"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert set(r.json()["recipients"]) == set(["c@example.com"])

    sent.clear()
    # filter=unpaid with unpaid_mode=no_paid: users with no paid entries -> u2 and u3 (u2 has no entries, u3 has unpaid only)
    r = client.post("/api/admin/broadcast", json={"subject": "S", "body": "B", "filter": "unpaid", "unpaid_mode": "no_paid"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert set(r.json()["recipients"]) == set(["b@example.com", "c@example.com"])

