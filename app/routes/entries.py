from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from app.db import get_db
from sqlalchemy.orm import Session
from app.services.entries import create_entry, get_entries_for_user, update_entry, delete_entry, EntryNameConflict
from app.routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


class EntryCreateSchema(BaseModel):
    week_id: int
    name: str
    picks: Any


class EntryUpdateSchema(BaseModel):
    name: str | None = None
    picks: Any | None = None


@router.post("/api/entries", status_code=201)
def post_entry(payload: EntryCreateSchema, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        entry = create_entry(db, current_user.id, payload.week_id, payload.picks, name=payload.name)
        return {"id": entry.id}
    except EntryNameConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/users/{user_id}/entries")
def list_user_entries(user_id: int, db: Session = Depends(get_db)):
    entries = get_entries_for_user(db, user_id)
    return [{"id": e.id, "week_id": e.week_id, "picks": e.picks} for e in entries]


@router.patch("/api/entries/{entry_id}")
def patch_entry(entry_id: int, payload: EntryUpdateSchema, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        updated = update_entry(db, entry_id, current_user.id, picks=payload.picks, name=payload.name)
        if not updated:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"id": updated.id}
    except EntryNameConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/entries/{entry_id}")
def remove_entry(entry_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        ok = delete_entry(db, entry_id, current_user.id)
        if not ok:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
