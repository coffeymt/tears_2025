from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
import hashlib

from ..db import get_db
from ..models.user import User
from ..models.password_reset import PasswordResetToken
from ..utils.email import send_email
from ..utils.security import get_password_hash
from ..schemas.auth import Token

router = APIRouter(prefix="/api/password-reset", tags=["password-reset"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/request")
def request_password_reset(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    # Respond 200 even if user not found to avoid user enumeration
    if not user:
        return {"ok": True}

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = PasswordResetToken.make_expiration(hours=1)

    pr = PasswordResetToken(token_hash=token_hash, user_id=user.id, expires_at=expires_at)
    db.add(pr)
    db.commit()

    reset_link = f"https://example.com/reset-password?token={raw_token}"
    body = f"Click the link to reset your password: {reset_link}\nThis link expires in 1 hour."

    try:
        send_email(user.email, "Password reset", body)
    except Exception:
        # Log in real app
        pass

    return {"ok": True}


@router.post("/submit")
def submit_password_reset(token: str, new_password: str, db: Session = Depends(get_db)):
    token_hash = _hash_token(token)
    pr = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    if not pr or pr.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == pr.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user.hashed_password = get_password_hash(new_password)
    db.delete(pr)
    db.commit()

    return {"ok": True}
