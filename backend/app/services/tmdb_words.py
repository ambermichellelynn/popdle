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
WORD_LEN = 5
WORD_RE = re.compile(r"^[A-Za-z]+$")

FALLBACK_WORDS: dict[Category, list[tuple[str, str]]] = {
    Category.movie: [
        ("MOANA", "Disney voyage across the Pacific"),
        ("SHREK", "Green ogre, big personality"),
        ("JOKER", "Joaquin Phoenix's Oscar-winning villain"),
        ("ALIEN", "Sci-fi horror — \"in space, no one can hear you scream\""),
        ("GHOST", "Patrick Swayze pottery scene, 1990"),
        ("ROCKY", "Philadelphia boxer's underdog story"),
        ("CRASH", "Best Picture winner, 2005"),
        ("BRAVE", "Pixar archer princess of Scotland"),
        ("AKIRA", "Landmark 1988 Japanese animated film"),
        ("TENET", "Christopher Nolan's time-inverting thriller"),
        ("ZORRO", "Masked swordsman of old California"),
        ("BAMBI", "Disney fawn who loses his mother"),
    ],
    Category.tv: [
        ("ARROW", "Vigilante archer of Star City"),
        ("ALIAS", "Spy drama starring Jennifer Garner"),
        ("HOUSE", "Misanthropic diagnostician, M.D."),
        ("BONES", "Forensic anthropologist procedural"),
        ("CHUCK", "Nerd Herd employee turned spy"),
        ("FARGO", "Anthology crime drama set in the Midwest"),
        ("GIRLS", "Lena Dunham's HBO comedy-drama"),
        ("ROOTS", "Landmark miniseries on American slavery"),
    ],
    Category.actor: [
        ("HANKS", "Forrest Gump and Cast Away star"),
        ("WATTS", "Naomi ___, King Kong and The Ring"),
        ("CLOSE", "Glenn ___, Fatal Attraction"),
        ("BACON", "Kevin ___, six degrees of separation"),
        ("SMITH", "Will ___, Fresh Prince to Men in Black"),
        ("DAVIS", "Viola ___, Fences and The Help"),
        ("STONE", "Emma ___, La La Land's Oscar winner"),
        ("BERRY", "Halle ___, first Black Best Actress winner"),
        ("FONDA", "Jane ___, activist and Klute star"),
    ],
}


def _clean_word(raw: str) -> str | None:
    word = raw.strip().upper()
    if len(word) == WORD_LEN and WORD_RE.match(word):
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


def pick_daily_word(seed: str, excluded: set[str] | None = None) -> tuple[str, str, Category]:
    """Deterministically picks a category + word for a given date seed (e.g. '2026-06-27').

    `excluded` lets callers avoid repeating recently-used answers (e.g. across the
    visible archive window); falls back to allowing a repeat only if every
    candidate in the chosen category has already been used.
    """
    rng = random.Random(seed)
    category = rng.choice(list(Category))
    candidates = fetch_candidates(category)
    if excluded:
        unused = [c for c in candidates if c[0] not in excluded]
        if unused:
            candidates = unused
    word, clue = rng.choice(candidates)
    return word, clue, category
