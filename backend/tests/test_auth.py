def test_signup_success(client, make_user):
    user_id = make_user()
    resp = client.post(
        "/users/signup",
        json={"user_id": user_id, "email": "amber@example.com", "password": "hunter2pass"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "amber@example.com"
    assert body["id"] == user_id


def test_signup_rejects_short_password(client, make_user):
    user_id = make_user()
    resp = client.post(
        "/users/signup",
        json={"user_id": user_id, "email": "amber@example.com", "password": "short"},
    )
    assert resp.status_code == 400


def test_signup_rejects_duplicate_email_for_different_user(client, make_user):
    first_user = make_user()
    client.post(
        "/users/signup",
        json={"user_id": first_user, "email": "shared@example.com", "password": "hunter2pass"},
    )

    second_user = make_user()
    resp = client.post(
        "/users/signup",
        json={"user_id": second_user, "email": "shared@example.com", "password": "anotherpass"},
    )
    assert resp.status_code == 409


def test_signup_unknown_user_id_404s(client):
    resp = client.post(
        "/users/signup",
        json={"user_id": "does-not-exist", "email": "amber@example.com", "password": "hunter2pass"},
    )
    assert resp.status_code == 404


def test_login_success(client, make_user):
    user_id = make_user()
    client.post(
        "/users/signup",
        json={"user_id": user_id, "email": "amber@example.com", "password": "hunter2pass"},
    )

    resp = client.post("/users/login", json={"email": "amber@example.com", "password": "hunter2pass"})
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


def test_login_wrong_password_rejected(client, make_user):
    user_id = make_user()
    client.post(
        "/users/signup",
        json={"user_id": user_id, "email": "amber@example.com", "password": "hunter2pass"},
    )

    resp = client.post("/users/login", json={"email": "amber@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email_rejected(client):
    resp = client.post("/users/login", json={"email": "ghost@example.com", "password": "whatever1"})
    assert resp.status_code == 401


def test_login_against_anonymous_account_without_password_rejected(client, make_user):
    make_user()
    resp = client.post(
        "/users/login", json={"email": "doesnotmatter@example.com", "password": "whatever1"}
    )
    assert resp.status_code == 401
