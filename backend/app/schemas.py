from datetime import date, datetime

from pydantic import BaseModel

from app.models.models import Category


class GuessResult(BaseModel):
    guess: str
    correct_positions: list[int]
    present_letters: list[int]
    won: bool
    attempts_used: int
    game_over: bool
    answer: str | None = None


class TodayPuzzle(BaseModel):
    word_date: date
    category: Category
    clue: str
    word_length: int
    history: list[GuessResult] = []
    game_over: bool = False
    answer: str | None = None
    is_archive: bool = False


class GuessRequest(BaseModel):
    user_id: str
    guess: str
    word_date: date | None = None


class ArchiveEntry(BaseModel):
    word_date: date
    category: Category
    clue: str
    word_length: int
    played: bool
    game_over: bool = False
    won: bool | None = None


class HistoryEntry(BaseModel):
    word_date: date
    category: Category
    answer: str | None = None
    won: bool
    attempts_used: int
    game_over: bool


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
