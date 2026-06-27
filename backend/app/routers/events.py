from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Event
from app.schemas import EventCreate, EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut)
def record_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    event = Event(user_id=payload.user_id, name=payload.name, properties=payload.properties)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
