from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.entry import Entry
from app.utils import email as email_utils


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


def send_broadcast(db: Session, subject: str, body: str, filter_kind: str = "all", unpaid_mode: Optional[str] = None) -> List[str]:
    """Send broadcast emails and return list of recipient emails.

    filter_kind: 'all' | 'active' | 'unpaid'
    - 'all': all users (active or not)
    - 'active': users with is_active == True
    - 'unpaid': users who have at least one entry with is_paid == False
    """
    recipients = []
    if filter_kind == "all":
        users = db.query(User).all()
        recipients = [u.email for u in users if u.email]
    elif filter_kind == "active":
        users = db.query(User).filter(User.is_active == True).all()
        recipients = [u.email for u in users if u.email]
    elif filter_kind == "unpaid":
        if unpaid_mode in (None, "any"):
            # Find non-admin users who have at least one unpaid entry
            q = db.query(User).join(Entry, Entry.user_id == User.id).filter(Entry.is_paid == False, User.is_admin == False).distinct()
            users = q.all()
            recipients = [u.email for u in users if u.email]
        elif unpaid_mode == "no_paid":
            # Users who have NO paid entries (i.e., not in the set of users with paid entries)
            paid_users_q = db.query(Entry.user_id).filter(Entry.is_paid == True).distinct()
            users = db.query(User).filter(~User.id.in_(paid_users_q), User.is_admin == False).all()
            recipients = [u.email for u in users if u.email]
        else:
            raise ValueError("Unknown unpaid_mode")
    else:
        raise ValueError("Unknown filter_kind")

    # Send email to each recipient; keep track of successes
    sent = []
    for to in recipients:
        # send_email may raise in real env; tests will mock it
        email_utils.send_email(to=to, subject=subject, body=body)
        sent.append(to)

    return sent
