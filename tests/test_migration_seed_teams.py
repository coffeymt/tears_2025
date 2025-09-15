import os
import importlib
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, Integer, String, create_engine


def test_migration_seeds_32(tmp_path, monkeypatch):
    # Create temporary sqlite DB for the migration test
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    metadata = MetaData()
    teams = Table(
        "teams",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("abbreviation", String, unique=True, nullable=False),
        Column("name", String),
        Column("city", String),
        Column("conference", String),
        Column("division", String),
    )
    metadata.create_all(engine)

    conn = engine.connect()

    # Monkeypatch alembic.op.get_bind to return our connection
    import alembic.op as alembic_op

    monkeypatch.setattr(alembic_op, "get_bind", lambda: conn)

    # Import the migration module by file path and run its upgrade function directly
    import importlib.util
    import pathlib

    repo_root = pathlib.Path(os.getcwd())
    mig_path = repo_root / "alembic" / "versions" / "20250915_seed_32_teams.py"
    spec = importlib.util.spec_from_file_location("seed_32_migration", str(mig_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.upgrade()

    # Verify the teams table has 32 rows
    result = conn.execute(sa.text("SELECT count(*) FROM teams")).fetchone()
    conn.close()
    engine.dispose()
    assert result is not None and result[0] == 32
