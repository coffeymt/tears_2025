import os
import sys
import pytest
from httpx import AsyncClient


async def create_user_and_get_token(client, email, password, is_admin=False, engine=None):
    # register
    await client.post("/api/auth/register", json={"email": email, "password": password})
    # set admin flag directly in DB
    if engine is not None:
        # Use ORM session to update the user
        from app.db import get_db
        from app.models.user import User

        db = next(get_db())
        u = db.query(User).filter(User.email == email).first()
        if u:
            u.is_admin = bool(is_admin)
            db.add(u)
            db.commit()
    # login
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    data = r.json()
    return data["access_token"]


@pytest.mark.asyncio
async def test_admin_weeks_flow(tmp_path):
    # Ensure project root is on sys.path before importing app modules
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Use a temporary sqlite DB for this test
    db_file = tmp_path / "test_admin_weeks.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"

    # import app modules after configuring env
    from app.main import app
    from app.models.base import Base
    from app.db import engine

    # prepare DB
    Base.metadata.create_all(bind=engine)

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_token = await create_user_and_get_token(client, "user@example.com", "pass123", is_admin=False, engine=engine)
        admin_token = await create_user_and_get_token(client, "admin@example.com", "pass123", is_admin=True, engine=engine)

        # non-admin cannot create week
        r = await client.post("/api/weeks/", json={"season_year": 2025, "week_number": 1}, headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 403

        # admin can create week
        r = await client.post("/api/weeks/", json={"season_year": 2025, "week_number": 1}, headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        week = r.json()
        week_id = week["id"]

        # validate that list fields are returned as lists
        assert isinstance(week.get("ineligible_teams"), list)
        assert isinstance(week.get("locked_games"), list)

        # admin can set current week
        r = await client.post("/api/weeks/admin/set-current", params={"week_id": week_id}, headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 204

        # create a second week and set it current, previous should be unset
        r2 = await client.post("/api/weeks/", json={"season_year": 2025, "week_number": 2}, headers={"Authorization": f"Bearer {admin_token}"})
        assert r2.status_code == 200
        w2 = r2.json()
        r3 = await client.post("/api/weeks/admin/set-current", params={"week_id": w2['id']}, headers={"Authorization": f"Bearer {admin_token}"})
        assert r3.status_code == 204

        # fetch weeks and check only the second is current
        rlist = await client.get("/api/weeks/", headers={"Authorization": f"Bearer {admin_token}"})
        assert rlist.status_code == 200
        weeks = rlist.json()
        current_weeks = [w for w in weeks if w.get("is_current")]
        assert len(current_weeks) == 1
        assert current_weeks[0]["week_number"] == 2

        # non-admin cannot set current
        r_forbid = await client.post("/api/weeks/admin/set-current", params={"week_id": week_id}, headers={"Authorization": f"Bearer {user_token}"})
        assert r_forbid.status_code == 403

        # invalid week_id returns 404
        r_not_found = await client.post("/api/weeks/admin/set-current", params={"week_id": 9999}, headers={"Authorization": f"Bearer {admin_token}"})
        assert r_not_found.status_code == 404
