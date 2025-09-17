from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.entry import Entry


def list_users(db: Session) -> List[User]:
    return db.query(User).all()


def patch_user(db: Session, user_id: int, *, is_active: Optional[bool] = None, is_admin: Optional[bool] = None) -> Optional[User]:
    user = db.get(User, user_id)
    if user is None:
        return None
    if is_active is not None:
        user.is_active = is_active
    if is_admin is not None:
        user.is_admin = is_admin
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_entries(db: Session, user_id: Optional[int] = None, show_eliminated: Optional[bool] = None) -> List[Entry]:
    q = db.query(Entry)
    if user_id is not None:
        q = q.filter(Entry.user_id == user_id)
    if show_eliminated is not None:
        q = q.filter(Entry.is_eliminated == show_eliminated)
    return q.all()


def patch_entry_payment(db: Session, entry_id: int, is_paid: bool) -> Optional[Entry]:
    entry = db.get(Entry, entry_id)
    if entry is None:
        return None
    entry.is_paid = is_paid
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def patch_entry_elimination(db: Session, entry_id: int, is_eliminated: bool) -> Optional[Entry]:
    entry = db.get(Entry, entry_id)
    if entry is None:
        return None
    entry.is_eliminated = is_eliminated
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
