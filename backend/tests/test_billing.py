def test_checkout_session_is_simulated_without_stripe_key(client, make_user):
    user_id = make_user()
    resp = client.post("/billing/checkout-session", json={"user_id": user_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["simulated"] is True
    assert body["session_id"].startswith("simulated_")


def test_checkout_session_unknown_user_404s(client):
    resp = client.post("/billing/checkout-session", json={"user_id": "does-not-exist"})
    assert resp.status_code == 404


def test_confirm_grants_premium_to_the_owning_user(client, make_user):
    user_id = make_user()
    session = client.post("/billing/checkout-session", json={"user_id": user_id}).json()

    resp = client.post(
        "/billing/confirm", json={"user_id": user_id, "session_id": session["session_id"]}
    )
    assert resp.status_code == 200
    assert resp.json()["is_premium"] is True

    user = client.post("/users/ensure", json={"user_id": user_id}).json()
    assert user["is_premium"] is True


def test_confirm_rejects_session_belonging_to_a_different_user(client, make_user):
    """A simulated session id created for user A must not grant premium to user B,
    even if B somehow obtains/guesses A's session id."""
    user_a = make_user()
    user_b = make_user()
    session = client.post("/billing/checkout-session", json={"user_id": user_a}).json()

    resp = client.post(
        "/billing/confirm", json={"user_id": user_b, "session_id": session["session_id"]}
    )
    assert resp.status_code == 400

    user_b_record = client.post("/users/ensure", json={"user_id": user_b}).json()
    assert user_b_record["is_premium"] is False


def test_confirm_with_bogus_session_id_rejected(client, make_user):
    user_id = make_user()
    resp = client.post(
        "/billing/confirm", json={"user_id": user_id, "session_id": "simulated_garbage"}
    )
    # "simulated_garbage" parses as owner_id "garbage", which won't match a real user id.
    assert resp.status_code == 400


def test_confirm_unknown_user_404s(client):
    resp = client.post(
        "/billing/confirm", json={"user_id": "does-not-exist", "session_id": "simulated_x:1"}
    )
    assert resp.status_code == 404
