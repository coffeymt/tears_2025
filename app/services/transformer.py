from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)


def _normalize_abbr(abbr: Any) -> str:
    if not abbr:
        return ""
    a = str(abbr).upper().strip()
    # Common ESPN -> canonical mappings
    mapping = {
        "WSH": "WAS",
        "JAC": "JAX",
        "LA": "LAR",
    }
    return mapping.get(a, a)


def _map_status(espn_state: Any) -> str:
    s = str(espn_state or "").lower()
    if s in ("pre", "pregame", "scheduled"):
        return "scheduled"
    if s in ("in", "inprogress"):
        return "in_progress"
    if s in ("post", "final"):
        return "final"
    return "scheduled"


def transform_espn_response(raw: Any) -> List[Dict]:
    """Transform ESPN scoreboard JSON to a list of internal game dicts.

    Returned dicts contain keys:
      - home_team_abbr, away_team_abbr, start_time (ISO str), status, home_score, away_score

    The transformer is defensive: it skips malformed events.
    """
    games: List[Dict] = []
    try:
        events = raw.get("events") if isinstance(raw, dict) else None
        if not isinstance(events, list):
            return []
    except Exception:
        return []

    for ev in events:
        try:
            competitions = ev.get("competitions") if isinstance(ev, dict) else []
            comp = competitions[0] if isinstance(competitions, list) and competitions else {}
            competitors = comp.get("competitors") if isinstance(comp, dict) else []
            if not isinstance(competitors, list) or len(competitors) < 2:
                continue

            home = next((c for c in competitors if isinstance(c, dict) and c.get("homeAway") == "home"), {})
            away = next((c for c in competitors if isinstance(c, dict) and c.get("homeAway") == "away"), {})

            home_team = (home.get("team") if isinstance(home, dict) else {}) or {}
            away_team = (away.get("team") if isinstance(away, dict) else {}) or {}

            home_abbr = _normalize_abbr(home_team.get("abbreviation"))
            away_abbr = _normalize_abbr(away_team.get("abbreviation"))
            if not home_abbr or not away_abbr:
                continue
            if len(home_abbr) < 2 or len(home_abbr) > 4 or len(away_abbr) < 2 or len(away_abbr) > 4:
                continue

            status = _map_status(ev.get("status", {}).get("type", {}).get("state")) if isinstance(ev, dict) else "scheduled"

            start_time = ev.get("date") if isinstance(ev, dict) else None
            # validate date
            if not start_time:
                continue

            # Scores may be nested on competitor objects
            try:
                home_score = int(home.get("score")) if home.get("score") is not None else None
            except Exception:
                home_score = None
            try:
                away_score = int(away.get("score")) if away.get("score") is not None else None
            except Exception:
                away_score = None

            games.append({
                "home_team_abbr": home_abbr,
                "away_team_abbr": away_abbr,
                "start_time": start_time,
                "status": status,
                "home_score": home_score,
                "away_score": away_score,
            })
        except Exception:
            # Skip problematic event
            continue

    return games
