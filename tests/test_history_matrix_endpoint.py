from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
import os


# Use the dev sqlite db by default if DATABASE_URL not set for tests
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")


def _get_test_db():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite:") else {})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_history_matrix_empty_db(monkeypatch):
    """When no weeks/entries/picks exist, endpoint should return empty weeks and entries list."""
    monkeypatch.setattr('app.routes.history.get_history_matrix', lambda db, season_year=None: {"weeks": [], "entries": []})
    client = TestClient(app)
    resp = client.get('/api/history/matrix')
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"weeks": [], "entries": []}
