import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

# Ensure project root is importable when running tests from pytest
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app

client = TestClient(app)


def test_sync_endpoint_forbidden():
    # No header provided
    resp = client.post("/internal/sync-games/espn?year=2025&week=1")
    assert resp.status_code == 403


@patch("app.routes.internal_sync.fetch_games_for_week")
@patch("app.routes.internal_sync.transform_and_sync_games")
def test_sync_endpoint_success(mock_sync, mock_fetch):
    # Provide the correct token via environment-configured settings
    from app.core.config import settings

    token = "test-token-123"
    # monkeypatch the settings object attribute
    settings.INTERNAL_SYNC_TOKEN = token

    mock_fetch.return_value = {"mock": "data"}
    resp = client.post(
        "/internal/sync-games/espn?year=2025&week=1",
        headers={"X-Internal-Sync-Token": token},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    mock_fetch.assert_called_once_with(year=2025, week=1)
    mock_sync.assert_called_once()

    # clean up
    settings.INTERNAL_SYNC_TOKEN = None
