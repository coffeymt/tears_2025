def test_seed_teams(tmp_path, monkeypatch):
    import sys, os

    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    # isolated sqlite DB
    db_file = tmp_path / "teams.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    from app.scripts.seed_teams import seed_teams
    from app.models.base import Base
    from app.models.team import Team
    from app.db import engine, SessionLocal

    # create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    seed_teams(db)

    count = db.query(Team).count()
    assert count == 32
