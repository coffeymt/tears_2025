import pytest
import asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_password_reset_flow(monkeypatch, tmp_path):
    # Ensure project root is on sys.path then import app modules
    import sys, os
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    # Use isolated sqlite DB for this test
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    from app.main import app
    from app.models.base import Base
    from app.db import engine, get_db
    from app.models.user import User
    from app.utils.security import get_password_hash, verify_password

    # Prepare DB
    Base.metadata.create_all(bind=engine)

    # Create user
    db = next(get_db())
    user = User(email="reset@example.com", hashed_password=get_password_hash("oldpass"))
    db.add(user)
    db.commit()
    db.refresh(user)

    sent = {}

    def fake_send_email(to, subject, body):
        import re

        m = re.search(r"token=([A-Za-z0-9_\-]+)", body)
        if m:
            sent["token"] = m.group(1)

    # Patch the function where the route imported it (app.routes.password_reset)
    monkeypatch.setattr("app.routes.password_reset.send_email", fake_send_email)

    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request reset
        resp = await client.post("/api/password-reset/request", params={"email": "reset@example.com"})
        assert resp.status_code == 200

        assert "token" in sent

        # Submit reset
        new_pass = "newsecret"
        resp2 = await client.post("/api/password-reset/submit", params={"token": sent["token"], "new_password": new_pass})
        assert resp2.status_code == 200

    # verify password changed
    db = next(get_db())
    u = db.query(User).filter(User.email == "reset@example.com").first()
    assert u is not None
    assert verify_password(new_pass, u.hashed_password)
