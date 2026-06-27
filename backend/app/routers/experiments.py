from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AssignmentOut
from app.services.experiments import assign_variant

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("/{experiment_key}/assignment", response_model=AssignmentOut)
def get_assignment(experiment_key: str, user_id: str, db: Session = Depends(get_db)) -> AssignmentOut:
    variant = assign_variant(db, user_id=user_id, experiment_key=experiment_key)
    return AssignmentOut(experiment_key=experiment_key, variant=variant)
