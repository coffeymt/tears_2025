from fastapi.testclient import TestClient
from app.main import app
from app.models.base import Base
from app.db import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.models.week import Week
from app.models.entry import Entry
from app.models.team import Team
from app.models.pick import Pick
import uuid


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")


def make_test_db():
    # Use an isolated in-memory SQLite DB shared across threads (StaticPool) so TestClient can see seeded data
    from sqlalchemy.pool import StaticPool
    test_db_url = "sqlite:///:memory:"
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        test_db_url,
        connect_args=connect_args,
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_history_matrix_integration():
    engine, SessionLocal = make_test_db()
    # make the FastAPI app use our testing session so requests see the seeded data
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    from app.db import get_db as _get_db
    app.dependency_overrides[_get_db] = override_get_db
    # seed data
    db = SessionLocal()
    try:
        # create a team with a unique abbreviation to avoid collisions in dev DB
        suffix = uuid.uuid4().hex[:8]
        abbr = f'TST{suffix}'
        team = Team(abbreviation=abbr, name=f'Test Team {suffix}', city='Test City', conference='A', division='X')
        db.add(team)
        db.commit()
        db.refresh(team)
        expected_team_id = team.id

        # create a week
        w = Week(season_year=2025, week_number=1)
        db.add(w)
        db.commit()
        db.refresh(w)

        # create a user so Entry.user_id FK is valid
        from app.models.user import User
        u = User(email=f'user_{suffix}@example.com', hashed_password='x')
        db.add(u)
        db.commit()
        db.refresh(u)

        # create an entry (Entry.week_id and picks are NOT NULL in the model)
        entry_name = f'Entry One {suffix}'
        e = Entry(user_id=u.id, week_id=w.id, name=entry_name, season_year=2025, picks=[])
        db.add(e)
        db.commit()
        db.refresh(e)

        # create a pick for that entry/week using raw SQL to avoid schema mismatches
        from sqlalchemy import text
        db.execute(
            text("INSERT INTO picks (entry_id, week_id, team_id) VALUES (:entry_id, :week_id, :team_id)"),
            {"entry_id": e.id, "week_id": w.id, "team_id": team.id},
        )
        db.commit()

    finally:
        db.close()

    client = TestClient(app)
    resp = client.get('/api/history/matrix?season_year=2025')
    assert resp.status_code == 200
    data = resp.json()
    assert data['weeks'] == [1]
    assert len(data['entries']) == 1
    entry = data['entries'][0]
    assert entry['entry_name'] == entry_name
    # picks should be list with one element equal to the team id we stored earlier
    assert entry['picks'] == [expected_team_id]
