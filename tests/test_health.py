import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure project root is importable when running tests from pytest
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.mark.asyncio
async def test_health_endpoint():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
