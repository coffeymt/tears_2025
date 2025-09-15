from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate, UserOut, Token
from app.models.user import User
from app.db import get_db
from app.utils import security
from pydantic import EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # simple uniqueness check
    exists = db.query(User).filter(User.email == user_in.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_in.email, hashed_password=security.get_password_hash(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = security.create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(credentials: "HTTPAuthorizationCredentials" = Depends(__import__("fastapi").security.HTTPBearer()), db: Session = Depends(get_db)):
    # credentials is provided by HTTPBearer() dependency and contains the token in `.credentials`
    from fastapi.security import HTTPAuthorizationCredentials

    creds: HTTPAuthorizationCredentials = credentials  # type: ignore
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = security.decode_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
