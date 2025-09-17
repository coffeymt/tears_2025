from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entry import Entry
from app.models.week import Week
from app.models.pick import Pick
from app.models.team import Team
from datetime import datetime, timezone
import time

# Simple in-memory TTL cache for current week info to avoid repeated DB hits during
# a short window. Tests and production calls will tolerate a small TTL.
_WEEK_INFO_CACHE: Optional[Dict[str, Any]] = None
_WEEK_INFO_CACHE_EXPIRY: float = 0.0
_WEEK_INFO_TTL_SECONDS = 1.0  # low TTL to keep tests predictable


def get_entries_for_user(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Return a list of entries owned by the user with minimal fields.

    Each entry dict contains: id, name, is_eliminated
    """
    rows = db.query(Entry).filter(Entry.user_id == user_id).all()
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "name": r.name,
            "is_eliminated": bool(getattr(r, "is_eliminated", False)),
        })
    return result


def get_current_week_info(db: Session) -> Optional[Dict[str, Any]]:
    """Return the current week info (id, number, lock_time, countdown_seconds) or None.

    countdown_seconds is computed relative to UTC now.
    """
    # Check cache first
    global _WEEK_INFO_CACHE, _WEEK_INFO_CACHE_EXPIRY
    now_ts = time.time()
    if _WEEK_INFO_CACHE is not None and now_ts < _WEEK_INFO_CACHE_EXPIRY:
        return _WEEK_INFO_CACHE

    w = db.query(Week).filter(Week.is_current == True).first()
    if not w:
        return None
    lock_time = w.lock_time
    now = datetime.now(timezone.utc)
    if lock_time is None:
        countdown = None
    else:
        # Ensure timezone-aware comparison
        if lock_time.tzinfo is None:
            lock_time = lock_time.replace(tzinfo=timezone.utc)
        countdown = int((lock_time - now).total_seconds())
    ret = {
        "week_id": w.id,
        "week_number": w.week_number,
        "lock_time": lock_time,
        "countdown_seconds": countdown,
    }

    # populate cache
    _WEEK_INFO_CACHE = ret
    _WEEK_INFO_CACHE_EXPIRY = time.time() + _WEEK_INFO_TTL_SECONDS
    return ret


def get_picks_for_entries(db: Session, entry_ids: List[int], week_id: int) -> Dict[int, Optional[Dict[str, Any]]]:
    """Return a mapping of entry_id -> pick info for the specified week.

    If an entry has no pick for the week, its value will be None.

    The pick info dict contains: team_id, team_abbr, team_name
    """
    # Guard against empty input
    result: Dict[int, Optional[Dict[str, Any]]] = {eid: None for eid in entry_ids}
    if not entry_ids:
        return result

    # Single efficient query joining picks -> teams for the given entries and week
    rows = (
        db.query(Pick, Team)
        .join(Team, Team.id == Pick.team_id)
        .filter(Pick.entry_id.in_(entry_ids), Pick.week_id == week_id)
        .all()
    )

    for pick, team in rows:
        result[pick.entry_id] = {
            "team_id": pick.team_id,
            "team_abbr": getattr(team, "abbreviation", None),
            "team_name": getattr(team, "name", None),
        }

    return result
