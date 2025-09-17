from typing import Any
import logging
from datetime import datetime

from app.services.transformer import transform_espn_response

logger = logging.getLogger(__name__)


def transform_and_sync_games(raw: Any, year: int, week: int, db):
    """Top-level orchestration: transform the raw payload and persist games.

    Persistence strategy: delete existing games for the week, insert new set, all in a single transaction.
    """
    games = transform_espn_response(raw)

    # Find the week record
    from app.models.week import Week
    from app.models.game import Game

    # Fetch the target week. Use an ordered query and defensively handle the case where
    # multiple Week rows for the same season/week exist (which can happen in local dev DBs).
    q = db.query(Week).filter(Week.season_year == year, Week.week_number == week)
    # Order by id descending so the most recently inserted matching Week is preferred.
    q_ordered = q.order_by(Week.id.desc())
    candidates = q_ordered.limit(2).all()
    if not candidates:
        raise ValueError(f"Week not found for season {year} week {week}")
    if len(candidates) > 1:
        logger.warning("Multiple Week rows found for %d-%d; using latest id=%s", year, week, candidates[0].id)
    target_week = candidates[0]

    # Normalize rows to insert
    rows = []
    for g in games:
        st = g.get("start_time")
        # Convert ISO strings to datetime objects for DB compatibility (SQLite requires datetime/date objects)
        if isinstance(st, str):
            try:
                # Handle trailing Z (UTC) by replacing with +00:00 for fromisoformat
                if st.endswith("Z"):
                    st_dt = datetime.fromisoformat(st.replace("Z", "+00:00"))
                else:
                    st_dt = datetime.fromisoformat(st)
            except Exception:
                # Fallback: try common format
                try:
                    st_dt = datetime.strptime(st, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    st_dt = None
        elif isinstance(st, datetime):
            st_dt = st
        else:
            st_dt = None

        rows.append({
            "week_id": target_week.id,
            "start_time": st_dt,
            "home_team_abbr": g.get("home_team_abbr"),
            "away_team_abbr": g.get("away_team_abbr"),
            "status": g.get("status") or "scheduled",
            "home_score": g.get("home_score"),
            "away_score": g.get("away_score"),
        })

    created = 0
    # Transactional delete-then-insert
    try:
        # Use a nested transaction (SAVEPOINT) if the session is already in a transaction,
        # otherwise begin a regular transaction. This allows callers that already started
        # a transaction to call this function safely (e.g. during tests).
        if db.in_transaction():
            tx_ctx = db.begin_nested()
        else:
            tx_ctx = db.begin()

        with tx_ctx:
            # Delete existing games for this week
            db.query(Game).filter(Game.week_id == target_week.id).delete(synchronize_session=False)
            # Insert new games
            for r in rows:
                g = Game(**r)
                db.add(g)
                created += 1
        logger.info("Synced %d games for %d-%d", created, year, week)
    except Exception:
        logger.exception("Failed to sync games for %d-%d", year, week)
        raise

    return {"created": created, "total_incoming": len(rows)}
