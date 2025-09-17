import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
DEFAULT_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"


def requests_session_with_retries(
    retries: int = 3, backoff_factor: float = 0.3, status_forcelist: tuple = (500, 502, 503, 504)
):
    """Create a requests.Session configured with urllib3 Retry behavior.

    Returns a session usable by callers. Tests may pass a custom session to
    `fetch_games_for_week` to avoid network calls.
    """
    # Local imports to avoid requiring `requests`/`urllib3` at module import time
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_games_for_week(year: int, week: int, session: Optional[Any] = None) -> Any:
    """Fetch raw ESPN game data for a specific year and week.

    Parameters:
      - year, week: ints to add to the scoreboard query
      - session: optional `requests.Session` to use (useful for testing/mocking)

    The base URL can be overridden with the `ESPN_BASE_URL` environment variable
    or by setting `core.config.ESPN_BASE_URL` in your application config.
    """
    if session is None:
        session = requests_session_with_retries()

    base = os.environ.get("ESPN_BASE_URL") or DEFAULT_BASE_URL
    url = f"{base}?week={week}&year={year}"
    logger.debug("Fetching ESPN scoreboard: %s", url)
    resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()
