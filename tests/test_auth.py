import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.mark.asyncio
async def test_register_and_login_flow(tmp_path, monkeypatch):
    # ensure using sqlite dev DB in temp location
    # set DATABASE_URL before importing app so Settings picks it up
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from app.main import app
    # create DB tables for the temporary sqlite DB
    from app.models.base import Base
    from app.db import engine

    Base.metadata.create_all(bind=engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # register
        resp = await ac.post("/api/auth/register", json={"email": "a@example.com", "password": "secret"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "a@example.com"

        # login
        resp = await ac.post("/api/auth/login", json={"email": "a@example.com", "password": "secret"})
        assert resp.status_code == 200
        token = resp.json().get("access_token")
        assert token

        # me
        headers = {"Authorization": f"Bearer {token}"}
        resp = await ac.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        me = resp.json()
        assert me["email"] == "a@example.com"
