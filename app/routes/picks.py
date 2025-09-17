from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db import get_db
from sqlalchemy.orm import Session
from app.routes.auth import get_current_user
from app.services.picks import create_pick, update_pick, PickConflict, WeekLockedError

router = APIRouter()


class PickCreateSchema(BaseModel):
    entry_id: int
    week_id: int
    team_id: int


class PickUpdateSchema(BaseModel):
    team_id: int


@router.post("/api/picks", status_code=201)
def post_pick(payload: PickCreateSchema, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        pick = create_pick(db, current_user.id, payload.entry_id, payload.week_id, payload.team_id)
        return {"id": pick.id}
    except PickConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except WeekLockedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        # ownership/validation problems
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/api/picks/{pick_id}")
def patch_pick(pick_id: int, payload: PickUpdateSchema, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        updated = update_pick(db, current_user.id, pick_id, payload.team_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Pick not found")
        return {"id": updated.id}
    except PickConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except WeekLockedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
