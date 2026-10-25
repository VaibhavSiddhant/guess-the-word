import os
import tempfile

# must be set before the app is imported
_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


_n = iter("abcdefghijklmnopqrstuvwxyz")


@pytest.fixture
def player(client):
    """A freshly registered player: (username, auth headers)."""
    name = "Player" + "".join(next(_n) for _ in range(3))
    r = client.post("/api/auth/register", json={"username": name, "password": "pass$123"})
    assert r.status_code == 201
    return name, {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture
def admin(client):
    r = client.post("/api/auth/login", json={"username": "Admin", "password": "Admin$123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}
