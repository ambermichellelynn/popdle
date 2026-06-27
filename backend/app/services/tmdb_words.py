"""Pulls pop-culture words (movie titles, TV titles, actor surnames) from TMDb.

Wordle-style boards need a single alphabetic word, so multi-word titles and
names are filtered out. Falls back to a small curated list if the TMDb API
key is missing or a request fails, so local dev doesn't require a key.
"""

import random
import re

import httpx

from app.config import settings
from app.models.models import Category

TMDB_BASE = "https://api.themoviedb.org/3"
MIN_LEN, MAX_LEN = 4, 8
WORD_RE = re.compile(r"^[A-Za-z]+$")

FALLBACK_WORDS: dict[Category, list[tuple[str, str]]] = {
    Category.movie: [("AVATAR", "Highest-grossing film of all time"), ("MOANA", "Disney voyage across the Pacific")],
    Category.tv: [("FRIENDS", "Six pals in a NYC coffee shop"), ("LOST", "Plane crash survivors on a mysterious island")],
    Category.actor: [("HANKS", "Forrest Gump and Cast Away star"), ("STREEP", "Most Oscar-nominated actor ever")],
}


def _clean_word(raw: str) -> str | None:
    word = raw.strip().upper()
    if MIN_LEN <= len(word) <= MAX_LEN and WORD_RE.match(word):
        return word
    return None


def _surname(full_name: str) -> str | None:
    parts = full_name.strip().split()
    return _clean_word(parts[-1]) if parts else None


def _fetch(endpoint: str) -> list[dict]:
    resp = httpx.get(
        f"{TMDB_BASE}/{endpoint}",
        params={"api_key": settings.tmdb_api_key, "language": "en-US", "page": random.randint(1, 5)},
        timeout=5.0,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def fetch_candidates(category: Category) -> list[tuple[str, str]]:
    """Returns (WORD, clue) pairs for a category, falling back to curated words on any failure."""
    if not settings.tmdb_api_key:
        return FALLBACK_WORDS[category]

    try:
        if category == Category.movie:
            results = _fetch("movie/popular")
            pairs = [(_clean_word(r["title"]), r.get("overview", "")[:120]) for r in results]
        elif category == Category.tv:
            results = _fetch("tv/popular")
            pairs = [(_clean_word(r["name"]), r.get("overview", "")[:120]) for r in results]
        else:
            results = _fetch("person/popular")
            pairs = [(_surname(r["name"]), f"Known for: {r.get('known_for_department', 'Acting')}") for r in results]

        candidates = [(word, clue) for word, clue in pairs if word]
        return candidates or FALLBACK_WORDS[category]
    except httpx.HTTPError:
        return FALLBACK_WORDS[category]


def pick_daily_word(seed: str) -> tuple[str, str, Category]:
    """Deterministically picks a category + word for a given date seed (e.g. '2026-06-27')."""
    rng = random.Random(seed)
    category = rng.choice(list(Category))
    candidates = fetch_candidates(category)
    word, clue = rng.choice(candidates)
    return word, clue, category
