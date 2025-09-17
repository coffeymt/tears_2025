from sqlalchemy.orm import Session
from app.models.entry import Entry
from app.models.week import Week
from app.models.pick import Pick
from datetime import datetime, timezone
from typing import Optional


class PickConflict(ValueError):
    pass


class WeekLockedError(ValueError):
    pass


def _is_week_locked(week: Week) -> bool:
    if not week.lock_time:
        return False
    lock = week.lock_time
    if lock.tzinfo is None:
        lock = lock.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= lock


def create_pick(db: Session, user_id: int, entry_id: int, week_id: int, team_id: int) -> Pick:
    # verify entry ownership
    entry = db.query(Entry).filter(Entry.id == entry_id).one_or_none()
    if not entry:
        raise ValueError("Entry not found")
    if entry.user_id != user_id:
        raise ValueError("Not authorized to pick for this entry")

    # verify week belongs to entry and lock status
    week = db.query(Week).filter(Week.id == week_id).one_or_none()
    if not week:
        raise ValueError("Week not found")
    if _is_week_locked(week):
        raise WeekLockedError("Week is locked - cannot submit picks")

    # ensure entry.week_id matches provided week_id
    if entry.week_id != week_id:
        raise ValueError("Entry does not belong to the provided week")

    # ensure team hasn't been previously picked by this entry this season
    # prevent the same user from picking the same team more than once in a season
    previous = db.query(Pick).join(Entry, Pick.entry_id == Entry.id).filter(Entry.user_id == entry.user_id, Entry.season_year == entry.season_year, Pick.team_id == team_id).one_or_none()
    if previous:
        raise PickConflict("Team already picked by this entry in the season")

    # enforce unique entry/week at DB level via constraint; handle duplicates gracefully
    existing = db.query(Pick).filter(Pick.entry_id == entry_id, Pick.week_id == week_id).one_or_none()
    if existing:
        raise PickConflict("Pick for this entry and week already exists; use PATCH to update")

    pick = Pick(entry_id=entry_id, week_id=week_id, team_id=team_id)
    db.add(pick)
    db.commit()
    db.refresh(pick)
    return pick


def update_pick(db: Session, user_id: int, pick_id: int, team_id: int) -> Optional[Pick]:
    pick = db.query(Pick).filter(Pick.id == pick_id).one_or_none()
    if not pick:
        return None
    # verify ownership through entry
    entry = db.query(Entry).filter(Entry.id == pick.entry_id).one_or_none()
    if not entry or entry.user_id != user_id:
        raise ValueError("Not authorized to modify this pick")

    week = db.query(Week).filter(Week.id == pick.week_id).one_or_none()
    if _is_week_locked(week):
        raise WeekLockedError("Week is locked - cannot modify picks")

    # ensure no repeat of team in season
    # prevent the same user from picking the same team more than once in a season (excluding current pick)
    previous = db.query(Pick).join(Entry, Pick.entry_id == Entry.id).filter(Entry.user_id == entry.user_id, Entry.season_year == entry.season_year, Pick.team_id == team_id, Pick.id != pick.id).one_or_none()
    if previous:
        raise PickConflict("Team already picked by this entry in the season")

    pick.team_id = team_id
    pick.updated_at = datetime.now(timezone.utc)
    db.add(pick)
    db.commit()
    db.refresh(pick)
    return pick
