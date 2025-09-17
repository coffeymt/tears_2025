from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.routes.auth import get_current_user
from app.services.dashboard import get_entries_for_user, get_current_week_info, get_picks_for_entries
from app.schemas.dashboard import DashboardResponse, EntrySummary, EntryPick, CurrentWeekInfo

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = current_user
    user_id = getattr(user, "id")

    entries = get_entries_for_user(db, user_id)
    entry_ids = [e["id"] for e in entries]

    week_info = get_current_week_info(db)
    picks_map = {}
    if week_info and week_info.get("week_id"):
        picks_map = get_picks_for_entries(db, entry_ids, week_info["week_id"]) if entry_ids else {}

    # Build EntrySummary objects
    entries_out: List[EntrySummary] = []
    for e in entries:
        pick = None
        if picks_map and e["id"] in picks_map and picks_map[e["id"]] is not None:
            p = picks_map[e["id"]]
            pick = EntryPick(team_id=p.get("team_id"), team_abbr=p.get("team_abbr"), team_name=p.get("team_name"))
        entries_out.append(EntrySummary(id=e["id"], name=e["name"], is_eliminated=e["is_eliminated"], current_pick=pick))

    current_week_obj = None
    if week_info:
        current_week_obj = CurrentWeekInfo(
            week_id=week_info.get("week_id"),
            week_number=week_info.get("week_number"),
            lock_time=week_info.get("lock_time"),
            countdown_seconds=week_info.get("countdown_seconds"),
        )

    resp = DashboardResponse(user_id=user_id, entries=entries_out, current_week=current_week_obj)
    return resp
