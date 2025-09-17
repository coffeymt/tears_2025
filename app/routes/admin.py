from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from app.routes.auth import require_admin
from app.db import get_db
from pydantic import BaseModel
from pydantic import ConfigDict

from app.services import admin as admin_svc

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserListOut(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserPatchPayload(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class EntryListOut(BaseModel):
    id: int
    user_id: int
    name: str
    is_eliminated: bool
    is_paid: bool

    model_config = ConfigDict(from_attributes=True)


class EntryPaymentPatch(BaseModel):
    is_paid: bool


class EntryEliminationPatch(BaseModel):
    is_eliminated: bool


@router.get("/users", response_model=List[UserListOut])
def list_users(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return admin_svc.list_users(db)


@router.patch("/users/{user_id}", response_model=UserListOut)
def patch_user(user_id: int, payload: UserPatchPayload, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    user = admin_svc.patch_user(db, user_id, is_active=payload.is_active, is_admin=payload.is_admin)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/entries", response_model=List[EntryListOut])
def list_entries(user_id: Optional[int] = None, show_eliminated: Optional[bool] = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return admin_svc.list_entries(db, user_id=user_id, show_eliminated=show_eliminated)


@router.patch("/entries/{entry_id}/payment", response_model=EntryListOut)
def patch_entry_payment(entry_id: int, payload: EntryPaymentPatch, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    entry = admin_svc.patch_entry_payment(db, entry_id, payload.is_paid)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router.patch("/entries/{entry_id}/elimination", response_model=EntryListOut)
def patch_entry_elimination(entry_id: int, payload: EntryEliminationPatch, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    entry = admin_svc.patch_entry_elimination(db, entry_id, payload.is_eliminated)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry
