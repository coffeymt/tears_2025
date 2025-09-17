import sys
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from fastapi.testclient import TestClient
from app.models.base import Base
from app.db import engine, SessionLocal
from app.models.week import Week
from app.models.game import Game


client = TestClient(app)


def test_site_time_returns_iso():
    resp = client.get("/api/public/site-time")
    assert resp.status_code == 200
    data = resp.json()
    assert "server_time" in data
    # parseable ISO
    datetime.fromisoformat(data["server_time"].replace("Z", "+00:00"))


def test_pre_reveal_for_week(tmp_path):
    # ensure DB schema exists
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        week = Week(season_year=2025, week_number=50, lock_time=datetime.now(timezone.utc) + timedelta(hours=1))
        db.add(week)
        db.commit()
        db.refresh(week)

        g = Game(week_id=week.id, start_time=datetime.now(timezone.utc) + timedelta(days=1), home_team_abbr="AAA", away_team_abbr="BBB")
        db.add(g)
        db.commit()
        db.refresh(g)

        resp = client.get(f"/api/public/pre-reveal/{week.id}")
        assert resp.status_code == 200
        j = resp.json()
        assert j["exists"] is True
        assert isinstance(j.get("games"), list)
        assert len(j["games"]) >= 1
        assert j["locked"] in (True, False)
    finally:
        db.close()
