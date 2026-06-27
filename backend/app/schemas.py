from datetime import date, datetime

from pydantic import BaseModel

from app.models.models import Category


class TodayPuzzle(BaseModel):
    word_date: date
    category: Category
    clue: str
    word_length: int


class GuessRequest(BaseModel):
    user_id: str
    guess: str


class GuessResult(BaseModel):
    guess: str
    correct_positions: list[int]
    present_letters: list[int]
    won: bool
    attempts_used: int
    game_over: bool
    answer: str | None = None


class EventCreate(BaseModel):
    user_id: str
    name: str
    properties: str | None = None


class EventOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentOut(BaseModel):
    experiment_key: str
    variant: str
