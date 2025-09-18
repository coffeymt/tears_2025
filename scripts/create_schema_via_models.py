"""
Create database schema in the target DATABASE_URL using SQLAlchemy model metadata.
This is a pragmatic step to ensure necessary tables exist when Alembic migrations are incomplete.

Usage:
$env:DATABASE_URL = "postgresql://..."
python .\scripts\create_schema_via_models.py

Warning: This will create tables as defined in `app.models.*` and may not match exact Alembic migrations.
Use only for dev/profiling when migrations are not available.
"""
import os
from sqlalchemy import create_engine

# Import application models so metadata includes all tables
from app.models.base import Base  # noqa
import app.models.user  # noqa
import app.models.team  # noqa
import app.models.week  # noqa
import app.models.entry  # noqa
import app.models.pick  # noqa
import app.models.game  # noqa


def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('Set DATABASE_URL in env')
        return
    engine = create_engine(database_url)
    print('Creating tables via metadata on', database_url.split('@')[-1])
    Base.metadata.create_all(bind=engine)
    print('Done')


if __name__ == '__main__':
    main()
