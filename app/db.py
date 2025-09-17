from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os
from typing import Generator


# Lazy engine/session handling: tests may set DATABASE_URL at runtime via environment vars.
# We keep a proxy engine object and recreate the real engine + sessionmaker when the
# configured DATABASE_URL changes.

_engine = None
_engine_url = None
_SessionLocal = None


def _create_engine_and_session(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    eng = create_engine(database_url, connect_args=connect_args)
    Sess = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return eng, Sess


def _ensure_engine():
    global _engine, _engine_url, _SessionLocal
    # Prefer environment variable if present, otherwise use settings (which reads .env)
    configured = os.environ.get("DATABASE_URL") or settings.DATABASE_URL or f"sqlite:///./dev.db"
    if _engine is None or configured != _engine_url:
        _engine, _SessionLocal = _create_engine_and_session(configured)
        _engine_url = configured


class _EngineProxy:
    def __getattr__(self, item):
        _ensure_engine()
        return getattr(_engine, item)


# Exported symbols
engine = _EngineProxy()


def SessionLocal():
    """Return a new Session instance bound to the current engine."""
    _ensure_engine()
    return _SessionLocal()


def get_db() -> Generator:
    _ensure_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
