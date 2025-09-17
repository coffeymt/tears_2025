from typing import Dict, Any, List
from app.models.entry import Entry
from app.models.week import Week
from app.models.user import User
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import delete
from typing import Optional


class EntryNameConflict(ValueError):
    pass


def create_entry(db: Session, user_id: int, week_id: int, picks: Any, name: str = None) -> Entry:
    # enforce week exists
    week = db.query(Week).filter(Week.id == week_id).one_or_none()
    if not week:
        raise ValueError("Week not found")
    # derive season from the week
    season = week.season_year

    # name is required
    if not name:
        raise ValueError("Entry name is required")

    # Enforce uniqueness: name per user per season
    conflict = db.query(Entry).filter(Entry.user_id == user_id, Entry.season_year == season, Entry.name == name).one_or_none()
    if conflict:
        # caller should treat this as a 409 conflict
        raise EntryNameConflict("Entry name already exists for this user in the season")

    # Enforce one entry per user/week - keep old behavior for picks overwrite
    existing = db.query(Entry).filter(Entry.user_id == user_id, Entry.week_id == week_id).one_or_none()
    if existing:
        existing.picks = picks
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    entry = Entry(user_id=user_id, week_id=week_id, name=name, season_year=season, picks=picks, created_at=datetime.utcnow())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_entries_for_user(db: Session, user_id: int) -> List[Entry]:
    return db.query(Entry).filter(Entry.user_id == user_id).all()


def _is_week_locked(week: Week) -> bool:
    if not week.lock_time:
        return False
    # naive compare using UTC datetimes consistent with other code in repo
    return datetime.utcnow() >= week.lock_time


def update_entry(db: Session, entry_id: int, user_id: int, picks: Any = None, name: str = None) -> Optional[Entry]:
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).one_or_none()
    if not entry:
        return None
    week = db.query(Week).filter(Week.id == entry.week_id).one_or_none()
    if _is_week_locked(week):
        raise ValueError("Week is locked - cannot modify entries")

    # handle rename: must ensure uniqueness per user/season
    if name and name != entry.name:
        conflict = db.query(Entry).filter(Entry.user_id == user_id, Entry.season_year == entry.season_year, Entry.name == name).one_or_none()
        if conflict:
            raise EntryNameConflict("Entry name already exists for this user in the season")
        entry.name = name

    if picks is not None:
        entry.picks = picks

    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: int, user_id: int) -> bool:
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).one_or_none()
    if not entry:
        return False
    week = db.query(Week).filter(Week.id == entry.week_id).one_or_none()
    if _is_week_locked(week):
        raise ValueError("Week is locked - cannot delete entries")
    db.delete(entry)
    db.commit()
    return True
