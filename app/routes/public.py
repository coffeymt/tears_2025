from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..db import get_db
from ..models.week import Week
from ..models.game import Game
from app.services.reveal import get_reveal_snapshot

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/site-time")
def site_time():
    """Return server current time (ISO 8601) and timezone info."""
    now = datetime.now(timezone.utc)
    return {"server_time": now.isoformat(), "timezone": "UTC"}


@router.get("/pre-reveal/{week_id}")
def pre_reveal(week_id: int, db: Session = Depends(get_db)):
    """Return a minimal pre-reveal view for a week: scheduled games (ids and team abbrs) and whether week is locked."""
    week = db.query(Week).filter(Week.id == week_id).one_or_none()
    if not week:
        return {"week_id": week_id, "exists": False}

    games = (
        db.query(Game)
        .filter(Game.week_id == week_id)
        .order_by(Game.start_time)
        .all()
    )

    games_out = [
        {
            "id": g.id,
            "start_time": (g.start_time.isoformat() if g.start_time else None),
            "home": g.home_team_abbr,
            "away": g.away_team_abbr,
            "status": g.status,
        }
        for g in games
    ]

    # Treat naive lock_time as UTC for compatibility
    locked = False
    if week.lock_time:
        lock = week.lock_time
        if lock.tzinfo is None:
            lock = lock.replace(tzinfo=timezone.utc)
        locked = datetime.now(timezone.utc) >= lock

    return {"week_id": week_id, "exists": True, "locked": locked, "games": games_out}


@router.get("/weeks/{week_id}/reveal-snapshot")
def reveal_snapshot(week_id: int, db: Session = Depends(get_db)):
    """Return aggregated reveal snapshot for a week once lock_time has passed. Publicly accessible.

    If the week doesn't exist, return 404-like payload `{"exists": False}`.
    """
    snapshot = get_reveal_snapshot(db, week_id)
    return snapshot
