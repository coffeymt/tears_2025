from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import InvalidRequestError
from typing import List
from app.db import get_db
from app.models.week import Week
from app.schemas.weeks import WeekCreate, WeekOut, WeekUpdate
from app.routes.auth import require_admin

router = APIRouter(prefix="/api/weeks", tags=["weeks"])


@router.post("/", response_model=WeekOut)
def create_week(week_in: WeekCreate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    week = Week(season_year=week_in.season_year, week_number=week_in.week_number)
    week.set_ineligible_teams(week_in.ineligible_teams or [])
    week.set_locked_games(week_in.locked_games or [])
    week.lock_time = week_in.lock_time
    db.add(week)
    db.commit()
    db.refresh(week)
    # SQLAlchemy JSON columns already provide Python lists; return directly
    return {
        "id": week.id,
        "season_year": week.season_year,
        "week_number": week.week_number,
        "is_current": week.is_current,
        "lock_time": week.lock_time,
        "ineligible_teams": week.get_ineligible_teams(),
        "locked_games": week.get_locked_games(),
    }


@router.get("/", response_model=List[WeekOut])
def list_weeks(db: Session = Depends(get_db)):
    rows = db.query(Week).order_by(Week.season_year.desc(), Week.week_number.desc()).all()
    result = []
    for w in rows:
        result.append(
            {
                "id": w.id,
                "season_year": w.season_year,
                "week_number": w.week_number,
                "is_current": w.is_current,
                "lock_time": w.lock_time,
                "ineligible_teams": w.get_ineligible_teams(),
                "locked_games": w.get_locked_games(),
            }
        )
    return result


@router.patch("/{week_id}", response_model=WeekOut)
def update_week(week_id: int, payload: WeekUpdate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    week = db.get(Week, week_id)
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")
    if payload.lock_time is not None:
        week.lock_time = payload.lock_time
    if payload.ineligible_teams is not None:
        week.set_ineligible_teams(payload.ineligible_teams)
    if payload.locked_games is not None:
        week.set_locked_games(payload.locked_games)
    if payload.is_current is not None:
        week.is_current = payload.is_current
    db.add(week)
    db.commit()
    db.refresh(week)
    return {
        "id": week.id,
        "season_year": week.season_year,
        "week_number": week.week_number,
        "is_current": week.is_current,
        "lock_time": week.lock_time,
        "ineligible_teams": week.get_ineligible_teams(),
        "locked_games": week.get_locked_games(),
    }


@router.post("/admin/set-current", status_code=204)
def set_current_week(week_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    # Perform the unset + set in a transaction to ensure atomicity
    # Use a nested transaction if a transaction is already active on the session
    tx_ctx = None
    try:
        if db.in_transaction():
            tx_ctx = db.begin_nested()
        else:
            tx_ctx = db.begin()
        with tx_ctx:
            # Unset previous current weeks
            db.query(Week).filter(Week.is_current == True).update({"is_current": False})
            # Fetch and set the requested week
            week = db.get(Week, week_id)
            if not week:
                # rollback happens automatically when leaving the context if an exception is raised
                raise HTTPException(status_code=404, detail="Week not found")
            week.is_current = True
            db.add(week)
    except InvalidRequestError:
        # Fallback: perform updates and commit if nested transaction semantics are unavailable
        db.query(Week).filter(Week.is_current == True).update({"is_current": False})
        week = db.get(Week, week_id)
        if not week:
            raise HTTPException(status_code=404, detail="Week not found")
        week.is_current = True
        db.add(week)
        db.commit()
    return None
