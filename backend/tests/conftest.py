import os

os.environ["DATABASE_URL"] = "postgresql://popdle:popdle@localhost:5432/popdle_test"
os.environ["TMDB_API_KEY"] = ""
os.environ["STRIPE_SECRET_KEY"] = ""
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_user(client):
    """Creates an anonymous user via the real /users/ensure endpoint and returns its id."""

    def _make() -> str:
        user_id = str(uuid.uuid4())
        resp = client.post("/users/ensure", json={"user_id": user_id})
        assert resp.status_code == 200
        return user_id

    return _make


@pytest.fixture
def premium_user(client, make_user):
    """Creates a user and upgrades them to premium via the simulated checkout flow."""

    def _make() -> str:
        user_id = make_user()
        session_resp = client.post("/billing/checkout-session", json={"user_id": user_id})
        session_id = session_resp.json()["session_id"]
        confirm_resp = client.post(
            "/billing/confirm", json={"user_id": user_id, "session_id": session_id}
        )
        assert confirm_resp.status_code == 200
        return user_id

    return _make
