from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User
from app.services.auth import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


class EnsureUserRequest(BaseModel):
    user_id: str


class SignupRequest(BaseModel):
    user_id: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    is_premium: bool

    class Config:
        from_attributes = True


@router.post("/ensure", response_model=UserOut)
def ensure_user(payload: EnsureUserRequest, db: Session = Depends(get_db)) -> User:
    """Idempotently creates an anonymous user record for a client-generated id."""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if user:
        return user
    user = User(id=payload.user_id, email=f"{payload.user_id}@anon.popdle.local")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/signup", response_model=UserOut)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> User:
    """Sets real credentials on the current anonymous user record, preserving its stats."""
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email and existing_email.id != payload.user_id:
        raise HTTPException(status_code=409, detail="An account with that email already exists")

    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email = payload.email
    user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> User:
    """Logs into an existing email/password account on this device."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user
