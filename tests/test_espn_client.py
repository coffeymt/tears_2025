import sys
import os
import pytest
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.services.espn_client import fetch_games_for_week, requests_session_with_retries


class DummyResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {"events": []}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self):
        return self._json


class DummySession:
    def __init__(self, resp: DummyResp):
        self.resp = resp
        self.last_url = None
        self.last_timeout = None

    def get(self, url, timeout=None):
        self.last_url = url
        self.last_timeout = timeout
        return self.resp


def test_fetch_games_success_with_session():
    dummy = DummyResp(200, {"events": ["ok"]})
    session = DummySession(dummy)
    res = fetch_games_for_week(2025, 1, session=session)
    assert res == {"events": ["ok"]}
    assert "week=1" in session.last_url and "year=2025" in session.last_url
    assert session.last_timeout == 10


def test_fetch_games_http_error_propagates():
    dummy = DummyResp(500, {})
    session = DummySession(dummy)
    with pytest.raises(Exception):
        fetch_games_for_week(2025, 1, session=session)


# Basic sanity test for session builder
def test_requests_session_with_retries_creates_session():
    # This test requires the `requests` package to be installed. Skip if not present.
    pytest.importorskip("requests")
    s = requests_session_with_retries(retries=1, backoff_factor=0)
    assert hasattr(s, "get")
