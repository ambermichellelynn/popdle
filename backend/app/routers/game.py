from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import DailyWord, GameAttempt, User
from app.schemas import (
    ArchiveEntry,
    GuessRequest,
    GuessResult,
    HistoryEntry,
    TodayPuzzle,
)
from app.services.tmdb_words import pick_daily_word
from app.services.validation import is_valid_uuid

router = APIRouter(prefix="/game", tags=["game"])

MAX_ATTEMPTS = 6
ARCHIVE_DAYS = 20


def _get_or_create_attempt(db: Session, user_id: str, daily_word_id: str) -> GameAttempt:
    if not is_valid_uuid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    attempt = (
        db.query(GameAttempt)
        .filter(GameAttempt.user_id == user_id, GameAttempt.daily_word_id == daily_word_id)
        .first()
    )
    if attempt:
        return attempt
    attempt = GameAttempt(
        user_id=user_id,
        daily_word_id=daily_word_id,
        guesses="",
        attempts_used=0,
        hints_used=0,
        won=False,
    )
    db.add(attempt)
    db.flush()
    return attempt


def _get_or_create_word_for_date(db: Session, target_date: date) -> DailyWord:
    daily_word = db.query(DailyWord).filter(DailyWord.word_date == target_date).first()
    if daily_word:
        return daily_word

    excluded = {row[0] for row in db.query(DailyWord.answer).all()}
    word, clue, category = pick_daily_word(seed=target_date.isoformat(), excluded=excluded)
    daily_word = DailyWord(word_date=target_date, answer=word, category=category, clue=clue)
    db.add(daily_word)
    db.commit()
    db.refresh(daily_word)
    return daily_word


def _require_user(db: Session, user_id: str) -> User:
    if not is_valid_uuid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _require_archive_access(db: Session, user_id: str, target_date: date) -> None:
    if target_date == date.today():
        return
    user = _require_user(db, user_id)
    if not user.is_premium:
        raise HTTPException(status_code=403, detail="Archived puzzles are a Premium feature")


def _score_guess(guess: str, answer: str) -> tuple[list[int], list[int]]:
    """Scores a guess against the answer, respecting letter frequency.

    A repeated letter in the guess can only be marked "present" as many times
    as it actually occurs (minus correct-position matches) in the answer —
    otherwise a guess like "TUTTI" against "LIGHT" would mark all three T's
    present instead of just the one the answer actually has.
    """
    correct_positions = [i for i, ch in enumerate(guess) if i < len(answer) and ch == answer[i]]

    remaining_letters = list(answer)
    for i in correct_positions:
        remaining_letters[i] = None

    present_letters = []
    for i, ch in enumerate(guess):
        if i in correct_positions:
            continue
        if ch in remaining_letters:
            present_letters.append(i)
            remaining_letters[remaining_letters.index(ch)] = None

    return correct_positions, present_letters


def _history_from_attempt(attempt: GameAttempt, answer: str) -> list[GuessResult]:
    results = []
    guesses = [g for g in attempt.guesses.split(",") if g]
    for guess in guesses:
        correct_positions, present_letters = _score_guess(guess, answer)
        results.append(
            GuessResult(
                guess=guess,
                correct_positions=correct_positions,
                present_letters=present_letters,
                won=guess == answer,
                attempts_used=0,
                game_over=False,
            )
        )
    return results


@router.get("/today", response_model=TodayPuzzle)
def get_today(
    user_id: str | None = None,
    date_str: str | None = None,
    db: Session = Depends(get_db),
) -> TodayPuzzle:
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    if target_date != date.today() and not user_id:
        raise HTTPException(status_code=403, detail="Archived puzzles are a Premium feature")
    if user_id:
        _require_archive_access(db, user_id, target_date)

    daily_word = _get_or_create_word_for_date(db, target_date)

    history: list[GuessResult] = []
    game_over = False
    if user_id:
        attempt = (
            db.query(GameAttempt)
            .filter(GameAttempt.user_id == user_id, GameAttempt.daily_word_id == daily_word.id)
            .first()
        )
        if attempt:
            history = _history_from_attempt(attempt, daily_word.answer)
            game_over = attempt.won or attempt.attempts_used >= MAX_ATTEMPTS

    return TodayPuzzle(
        word_date=daily_word.word_date,
        category=daily_word.category,
        clue=daily_word.clue or "",
        word_length=len(daily_word.answer),
        history=history,
        game_over=game_over,
        answer=daily_word.answer if game_over else None,
        is_archive=target_date != date.today(),
    )


@router.post("/guess", response_model=GuessResult)
def submit_guess(payload: GuessRequest, db: Session = Depends(get_db)) -> GuessResult:
    target_date = payload.word_date or date.today()
    _require_archive_access(db, payload.user_id, target_date)

    daily_word = _get_or_create_word_for_date(db, target_date)
    guess = payload.guess.strip().upper()

    if len(guess) != len(daily_word.answer):
        raise HTTPException(status_code=400, detail=f"Guess must be {len(daily_word.answer)} letters")
    if not guess.isalpha():
        raise HTTPException(status_code=400, detail="Guess must contain only letters")

    attempt = _get_or_create_attempt(db, payload.user_id, daily_word.id)

    if attempt.won or attempt.attempts_used >= MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail="Game already finished for this puzzle")

    correct_positions, present_letters = _score_guess(guess, daily_word.answer)
    won = guess == daily_word.answer

    attempt.guesses = ",".join(filter(None, [attempt.guesses, guess]))
    attempt.attempts_used += 1
    attempt.won = won
    game_over = won or attempt.attempts_used >= MAX_ATTEMPTS
    if game_over:
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


@router.get("/archive", response_model=list[ArchiveEntry])
def get_archive(user_id: str, db: Session = Depends(get_db)) -> list[ArchiveEntry]:
    user = _require_user(db, user_id)
    if not user.is_premium:
        raise HTTPException(status_code=403, detail="Archived puzzles are a Premium feature")

    entries = []
    for offset in range(1, ARCHIVE_DAYS + 1):
        target_date = date.today() - timedelta(days=offset)
        daily_word = _get_or_create_word_for_date(db, target_date)
        attempt = (
            db.query(GameAttempt)
            .filter(GameAttempt.user_id == user_id, GameAttempt.daily_word_id == daily_word.id)
            .first()
        )
        game_over = attempt is not None and (attempt.won or attempt.attempts_used >= MAX_ATTEMPTS)
        entries.append(
            ArchiveEntry(
                word_date=daily_word.word_date,
                category=daily_word.category,
                clue=daily_word.clue or "",
                word_length=len(daily_word.answer),
                played=attempt is not None and attempt.attempts_used > 0,
                game_over=game_over,
                won=attempt.won if game_over else None,
            )
        )
    return entries


@router.get("/history", response_model=list[HistoryEntry])
def get_history(user_id: str, db: Session = Depends(get_db)) -> list[HistoryEntry]:
    user = _require_user(db, user_id)
    if not user.is_premium:
        raise HTTPException(status_code=403, detail="Full stats history is a Premium feature")

    rows = (
        db.query(GameAttempt, DailyWord)
        .join(DailyWord, GameAttempt.daily_word_id == DailyWord.id)
        .filter(GameAttempt.user_id == user_id, GameAttempt.attempts_used > 0)
        .order_by(DailyWord.word_date.desc())
        .all()
    )
    return [
        HistoryEntry(
            word_date=daily_word.word_date,
            category=daily_word.category,
            answer=daily_word.answer if (attempt.won or attempt.attempts_used >= MAX_ATTEMPTS) else None,
            won=attempt.won,
            attempts_used=attempt.attempts_used,
            game_over=attempt.won or attempt.attempts_used >= MAX_ATTEMPTS,
        )
        for attempt, daily_word in rows
    ]
