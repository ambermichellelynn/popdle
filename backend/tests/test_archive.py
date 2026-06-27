def test_archive_requires_premium(client, make_user):
    user_id = make_user()
    resp = client.get("/game/archive", params={"user_id": user_id})
    assert resp.status_code == 403


def test_archive_returns_twenty_unique_dates_for_premium(client, premium_user):
    user_id = premium_user()
    resp = client.get("/game/archive", params={"user_id": user_id})
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 20
    dates = [e["word_date"] for e in entries]
    assert len(set(dates)) == 20
    assert all(e["played"] is False for e in entries)
    assert all(e["game_over"] is False for e in entries)
    assert all(e["won"] is None for e in entries)


def test_archive_reflects_in_progress_game(client, premium_user):
    user_id = premium_user()
    archive_date = client.get("/game/archive", params={"user_id": user_id}).json()[0]["word_date"]

    client.post(
        "/game/guess", json={"user_id": user_id, "guess": "ABCDE", "word_date": archive_date}
    )

    entry = next(
        e
        for e in client.get("/game/archive", params={"user_id": user_id}).json()
        if e["word_date"] == archive_date
    )
    assert entry["played"] is True
    assert entry["game_over"] is False
    assert entry["won"] is None


def test_archive_reflects_finished_game(client, premium_user):
    user_id = premium_user()
    archive_date = client.get("/game/archive", params={"user_id": user_id}).json()[0]["word_date"]

    last = None
    for _ in range(6):
        last = client.post(
            "/game/guess", json={"user_id": user_id, "guess": "ZZZZZ", "word_date": archive_date}
        )

    entry = next(
        e
        for e in client.get("/game/archive", params={"user_id": user_id}).json()
        if e["word_date"] == archive_date
    )
    assert entry["played"] is True
    assert entry["game_over"] is True
    assert entry["won"] is False
    assert last.json()["game_over"] is True


def test_history_requires_premium(client, make_user):
    user_id = make_user()
    resp = client.get("/game/history", params={"user_id": user_id})
    assert resp.status_code == 403


def test_history_empty_for_new_premium_user(client, premium_user):
    user_id = premium_user()
    resp = client.get("/game/history", params={"user_id": user_id})
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_includes_played_archive_game(client, premium_user):
    user_id = premium_user()
    archive_date = client.get("/game/archive", params={"user_id": user_id}).json()[0]["word_date"]
    client.post(
        "/game/guess", json={"user_id": user_id, "guess": "ABCDE", "word_date": archive_date}
    )

    resp = client.get("/game/history", params={"user_id": user_id})
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["word_date"] == archive_date
    assert entries[0]["attempts_used"] == 1
    assert entries[0]["game_over"] is False
