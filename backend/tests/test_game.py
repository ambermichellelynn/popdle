def test_get_today_without_user_returns_no_answer(client):
    resp = client.get("/game/today")
    assert resp.status_code == 200
    body = resp.json()
    assert body["word_length"] == 5
    assert body["answer"] is None
    assert body["history"] == []
    assert body["game_over"] is False


def test_get_today_is_deterministic_across_calls(client):
    first = client.get("/game/today").json()
    second = client.get("/game/today").json()
    assert first["word_date"] == second["word_date"]
    assert first["category"] == second["category"]
    assert first["clue"] == second["clue"]


def test_winning_guess_reveals_answer(client, make_user):
    user_id = make_user()
    puzzle = client.get("/game/today").json()
    answer = _solve_answer(client)

    resp = client.post("/game/guess", json={"user_id": user_id, "guess": answer})
    assert resp.status_code == 200
    body = resp.json()
    assert body["won"] is True
    assert body["game_over"] is True
    assert body["answer"] == answer
    assert body["correct_positions"] == list(range(puzzle["word_length"]))


def test_wrong_length_guess_is_rejected(client, make_user):
    user_id = make_user()
    resp = client.post("/game/guess", json={"user_id": user_id, "guess": "AB"})
    assert resp.status_code == 400


def test_non_alphabetic_guess_is_rejected(client, make_user):
    user_id = make_user()
    resp = client.post("/game/guess", json={"user_id": user_id, "guess": "12345"})
    assert resp.status_code == 400


def test_cannot_guess_after_game_over(client, make_user):
    user_id = make_user()
    answer = _solve_answer(client)
    client.post("/game/guess", json={"user_id": user_id, "guess": answer})

    resp = client.post("/game/guess", json={"user_id": user_id, "guess": answer})
    assert resp.status_code == 400


def test_six_wrong_guesses_ends_game_with_answer_revealed(client, make_user):
    user_id = make_user()
    answer = _solve_answer(client)
    wrong_guess = "ZZZZZ" if "ZZZZZ" != answer else "QQQQQ"

    last_response = None
    for _ in range(6):
        last_response = client.post("/game/guess", json={"user_id": user_id, "guess": wrong_guess})

    body = last_response.json()
    assert body["game_over"] is True
    assert body["won"] is False
    assert body["answer"] == answer


def test_guess_history_resumes_on_refetch(client, make_user):
    user_id = make_user()
    wrong_guess = "ABCDE"
    client.post("/game/guess", json={"user_id": user_id, "guess": wrong_guess})

    resp = client.get("/game/today", params={"user_id": user_id})
    body = resp.json()
    assert len(body["history"]) == 1
    assert body["history"][0]["guess"] == wrong_guess
    assert body["game_over"] is False


def test_archive_date_blocked_without_user_id(client):
    resp = client.get("/game/today", params={"date_str": "2020-01-01"})
    assert resp.status_code == 403


def test_archive_date_blocked_for_non_premium_user(client, make_user):
    user_id = make_user()
    resp = client.get("/game/today", params={"user_id": user_id, "date_str": "2020-01-01"})
    assert resp.status_code == 403


def test_archive_date_allowed_for_premium_user(client, premium_user):
    user_id = premium_user()
    resp = client.get("/game/today", params={"user_id": user_id, "date_str": "2020-01-01"})
    assert resp.status_code == 200
    assert resp.json()["is_archive"] is True


def test_guess_on_archive_date_blocked_for_non_premium(client, make_user):
    user_id = make_user()
    resp = client.post(
        "/game/guess",
        json={"user_id": user_id, "guess": "ABCDE", "word_date": "2020-01-01"},
    )
    assert resp.status_code == 403


def _solve_answer(client) -> str:
    """Cheats by reading the answer straight from the DB-backed fallback pool via a losing
    game, then asking the backend to reveal it — keeps the test independent of which word
    was picked for "today" without needing direct DB access."""
    user_id = "00000000-0000-0000-0000-000000000000"
    client.post("/users/ensure", json={"user_id": user_id})
    wrong_guess = "ZZZZZ"
    last = None
    for _ in range(6):
        last = client.post("/game/guess", json={"user_id": user_id, "guess": wrong_guess})
    return last.json()["answer"]
