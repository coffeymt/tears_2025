import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal, engine
from app.models.base import Base
from app.models.entry import Entry
from app.models.pick import Pick
from app.models.team import Team
from app.models.game import Game
from app.models.week import Week
import uuid
from datetime import datetime


def _create_week_and_game(db):
    week = Week(season_year=2025, week_number=1)
    db.add(week)
    db.commit()
    db.refresh(week)
    team_a = Team(abbreviation=f"AAA{uuid.uuid4().hex[:6]}", name="Team A")
    team_b = Team(abbreviation=f"BBB{uuid.uuid4().hex[:6]}", name="Team B")
    db.add_all([team_a, team_b])
    db.commit()
    db.refresh(team_a)
    db.refresh(team_b)
    game = Game(week_id=week.id, start_time=datetime(2025,9,1,12,0,0), home_team_abbr=team_a.abbreviation, away_team_abbr=team_b.abbreviation)
    db.add(game)
    db.commit()
    db.refresh(game)
    return week, game, team_a, team_b


def test_admin_finalize_endpoint_monkeypatch_admin(monkeypatch):
    # Ensure tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    week, game, team_a, team_b = _create_week_and_game(db)

    # create an entry and pick
    entry = Entry(user_id=1, week_id=week.id, name=f"int-e-{uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)
    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()

    # Use FastAPI dependency_overrides to bypass require_admin dependency
    from app.routes.admin_weeks import require_admin as require_admin_dep
    app.dependency_overrides[require_admin_dep] = lambda: True
    try:
        client = TestClient(app)
        payload = {"games": [{"game_id": game.id, "home_score": 21, "away_score": 14}]}
        resp = client.post(f"/api/admin/weeks/{week.id}/finalize-scores", json=payload)
    finally:
        # cleanup override
        app.dependency_overrides.pop(require_admin_dep, None)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"

    # confirm DB updated
    p = db.get(Pick, pick.id)
    assert p.result == "win"
    e = db.get(Entry, entry.id)
    assert getattr(e, "is_eliminated", False) is False

    db.close()
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.models.base import Base
from app.db import engine, SessionLocal
from sqlalchemy.orm import Session
from app.models.week import Week
from app.models.game import Game
from app.models.team import Team
from app.models.entry import Entry
from app.models.pick import Pick


def _create_admin_and_headers(db: Session):
    # Create admin user via direct DB manipulation for tests
    from app.models.user import User
    import uuid
    u = User(email=f"admin+{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", is_admin=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    # produce token using security.create_access_token
    from app.utils.security import create_access_token
    token = create_access_token(subject=str(u.id))
    return {"Authorization": f"Bearer {token}"}


def test_admin_finalize_endpoint():
    from app.db import engine, SessionLocal
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # create data
    week = Week(season_year=2025, week_number=1)
    db.add(week)
    db.commit()
    db.refresh(week)
    import uuid
    from datetime import datetime
    team_a = Team(abbreviation=f"AAA2{uuid.uuid4().hex[:6]}", name="Team A")
    team_b = Team(abbreviation=f"BBB2{uuid.uuid4().hex[:6]}", name="Team B")
    db.add_all([team_a, team_b])
    db.commit()
    db.refresh(team_a)
    db.refresh(team_b)
    game = Game(week_id=week.id, start_time=datetime(2025,9,1,12,0,0), home_team_abbr=team_a.abbreviation, away_team_abbr=team_b.abbreviation)
    db.add(game)
    db.commit()
    db.refresh(game)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"e1-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()
    db.refresh(pick)

    headers = _create_admin_and_headers(db)
    client = TestClient(app)

    payload = {"games": [{"game_id": game.id, "home_score": 10, "away_score": 3}]}
    resp = client.post(f"/api/admin/weeks/{week.id}/finalize-scores", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

    p = db.get(Pick, pick.id)
    assert p.result == "win"
    e = db.get(Entry, entry.id)
    assert getattr(e, "is_eliminated", False) == False


def test_admin_finalize_validation_rejects_bad_payload():
    from app.db import SessionLocal, engine
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)
    # create a minimal week
    week = Week(season_year=2025, week_number=99)
    db.add(week)
    db.commit()
    db.refresh(week)

    # make admin headers
    headers = _create_admin_and_headers(db)
    client = TestClient(app)

    # bad payload: games is not a list
    bad_payload = {"games": "not-a-list"}
    resp = client.post(f"/api/admin/weeks/{week.id}/finalize-scores", json=bad_payload, headers=headers)
    assert resp.status_code == 422
