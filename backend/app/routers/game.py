from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import DailyWord, GameAttempt
from app.schemas import GuessRequest, GuessResult, TodayPuzzle
from app.services.tmdb_words import pick_daily_word

router = APIRouter(prefix="/game", tags=["game"])

MAX_ATTEMPTS = 6


def _get_or_create_daily_word(db: Session) -> DailyWord:
    today = date.today()
    daily_word = db.query(DailyWord).filter(DailyWord.word_date == today).first()
    if daily_word:
        return daily_word

    word, clue, category = pick_daily_word(seed=today.isoformat())
    daily_word = DailyWord(word_date=today, answer=word, category=category, clue=clue)
    db.add(daily_word)
    db.commit()
    db.refresh(daily_word)
    return daily_word


@router.get("/today", response_model=TodayPuzzle)
def get_today(db: Session = Depends(get_db)) -> TodayPuzzle:
    daily_word = _get_or_create_daily_word(db)
    return TodayPuzzle(
        word_date=daily_word.word_date,
        category=daily_word.category,
        clue=daily_word.clue or "",
        word_length=len(daily_word.answer),
    )


def _score_guess(guess: str, answer: str) -> tuple[list[int], list[int]]:
    correct_positions = [i for i, ch in enumerate(guess) if i < len(answer) and ch == answer[i]]
    present_letters = [
        i for i, ch in enumerate(guess) if i not in correct_positions and ch in answer
    ]
    return correct_positions, present_letters


@router.post("/guess", response_model=GuessResult)
def submit_guess(payload: GuessRequest, db: Session = Depends(get_db)) -> GuessResult:
    daily_word = _get_or_create_daily_word(db)
    guess = payload.guess.strip().upper()

    if len(guess) != len(daily_word.answer):
        raise HTTPException(status_code=400, detail=f"Guess must be {len(daily_word.answer)} letters")

    attempt = (
        db.query(GameAttempt)
        .filter(GameAttempt.user_id == payload.user_id, GameAttempt.daily_word_id == daily_word.id)
        .first()
    )
    if not attempt:
        attempt = GameAttempt(user_id=payload.user_id, daily_word_id=daily_word.id, guesses="")
        db.add(attempt)

    if attempt.won or attempt.attempts_used >= MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail="Game already finished for today")

    correct_positions, present_letters = _score_guess(guess, daily_word.answer)
    won = guess == daily_word.answer

    attempt.guesses = ",".join(filter(None, [attempt.guesses, guess]))
    attempt.attempts_used += 1
    attempt.won = won
    game_over = won or attempt.attempts_used >= MAX_ATTEMPTS
    if game_over:
        from datetime import datetime

        attempt.finished_at = datetime.utcnow()

    db.commit()

    return GuessResult(
        guess=guess,
        correct_positions=correct_positions,
        present_letters=present_letters,
        won=won,
        attempts_used=attempt.attempts_used,
        game_over=game_over,
        answer=daily_word.answer if game_over else None,
    )
