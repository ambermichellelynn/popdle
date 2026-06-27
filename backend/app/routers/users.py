from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User

router = APIRouter(prefix="/users", tags=["users"])


class EnsureUserRequest(BaseModel):
    user_id: str


class UserOut(BaseModel):
    id: str
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
