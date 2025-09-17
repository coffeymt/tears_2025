from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.week import Week
from app.models.game import Game
from app.models.pick import Pick
from app.models.team import Team


def _as_utc(dt: datetime) -> datetime:
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_reveal_snapshot(db: Session, week_id: int) -> Dict[str, Any]:
    """Return a reveal snapshot for the given week.

    If now < week.lock_time, return a minimal payload with `locked: False` and
    basic counts (or empty games). If lock time has passed, return aggregated
    pick distribution per game/team, game results, and survivor counts.
    """
    week = db.execute(select(Week).where(Week.id == week_id)).scalar_one_or_none()
    if week is None:
        return {"exists": False}

    now = datetime.now(timezone.utc)
    lock_time = _as_utc(week.lock_time) if week.lock_time is not None else None

    # Base response
    resp: Dict[str, Any] = {
        "exists": True,
        "week_id": week_id,
        "locked": False,
        "games": [],
    }

    # Load games for the week
    games: List[Game] = db.execute(select(Game).where(Game.week_id == week_id).order_by(Game.start_time)).scalars().all()

    # Prepare team lookups by abbreviation and id for use in both branches
    team_abbrs = {abbr for g in games for abbr in (g.home_team_abbr, g.away_team_abbr) if abbr}
    teams_by_abbr = {}
    teams_by_id = {}
    if team_abbrs:
        team_rows = db.execute(select(Team).where(Team.abbreviation.in_(team_abbrs))).scalars().all()
        teams_by_abbr = {t.abbreviation: t for t in team_rows}
        teams_by_id = {t.id: t for t in team_rows}

    if lock_time is None or now < lock_time:
        # Return minimal info: games with limited fields (abbreviations + optional team ids)
        for g in games:
            home = teams_by_abbr.get(g.home_team_abbr)
            away = teams_by_abbr.get(g.away_team_abbr)
            resp["games"].append({
                "id": g.id,
                "start_time": g.start_time.isoformat() if g.start_time is not None else None,
                "home_team": {"abbr": g.home_team_abbr, "id": home.id if home else None, "name": home.name if home else None},
                "away_team": {"abbr": g.away_team_abbr, "id": away.id if away else None, "name": away.name if away else None},
                "status": g.status,
            })
        return resp

    # Past lock_time: produce aggregated snapshot
    resp["locked"] = True

    # Query picks aggregated by team across the week
    picks_count_query = (
        select(Pick.team_id, func.count().label("count"))
        .where(Pick.week_id == week_id)
        .group_by(Pick.team_id)
    )
    picks_rows = db.execute(picks_count_query).all()

    # Build mapping (team_id -> count)
    picks_map: Dict[int, int] = {}
    for team_id, count in picks_rows:
        picks_map[int(team_id)] = int(count)

    # Fetch team rows by abbreviation for display and id mapping
    team_abbrs = {abbr for g in games for abbr in (g.home_team_abbr, g.away_team_abbr) if abbr}
    teams_by_abbr = {}
    teams_by_id = {}
    if team_abbrs:
        team_rows = db.execute(select(Team).where(Team.abbreviation.in_(team_abbrs))).scalars().all()
        teams_by_abbr = {t.abbreviation: t for t in team_rows}
        teams_by_id = {t.id: t for t in team_rows}

    # Determine winners for games with final scores
    for g in games:
        home_team = teams_by_abbr.get(g.home_team_abbr)
        away_team = teams_by_abbr.get(g.away_team_abbr)

        game_entry: Dict[str, Any] = {
            "id": g.id,
            "start_time": g.start_time.isoformat() if g.start_time is not None else None,
            "home_team": {
                "id": home_team.id if home_team else None,
                "abbr": g.home_team_abbr,
                "name": home_team.name if home_team else None,
            },
            "away_team": {
                "id": away_team.id if away_team else None,
                "abbr": g.away_team_abbr,
                "name": away_team.name if away_team else None,
            },
            "status": g.status,
            "home_score": getattr(g, "home_score", None),
            "away_score": getattr(g, "away_score", None),
            # pick counts for teams in this game (by team id)
            "pick_counts": {
                (home_team.id if home_team else None): picks_map.get(home_team.id if home_team else None, 0),
                (away_team.id if away_team else None): picks_map.get(away_team.id if away_team else None, 0),
            },
            "winning_team_id": None,
        }

        if g.status == "final" and getattr(g, "home_score", None) is not None and getattr(g, "away_score", None) is not None:
            if g.home_score > g.away_score:
                game_entry["winning_team_id"] = home_team.id if home_team else None
            elif g.away_score > g.home_score:
                game_entry["winning_team_id"] = away_team.id if away_team else None
            else:
                game_entry["winning_team_id"] = None  # tie

        resp["games"].append(game_entry)

    # Compute survivors/losers by comparing picks to game winners when available
    # Build mapping from team abbreviation -> winning_team_id for final games
    abbr_to_winner: Dict[str, int] = {}
    for g in games:
        if g.status == "final":
            if getattr(g, "home_score", None) is not None and getattr(g, "away_score", None) is not None:
                if getattr(g, "home_score", 0) > getattr(g, "away_score", 0):
                    abbr_to_winner[g.home_team_abbr] = teams_by_abbr.get(g.home_team_abbr).id if teams_by_abbr.get(g.home_team_abbr) else None
                    abbr_to_winner[g.away_team_abbr] = teams_by_abbr.get(g.home_team_abbr).id if teams_by_abbr.get(g.home_team_abbr) else None
                elif getattr(g, "away_score", 0) > getattr(g, "home_score", 0):
                    abbr_to_winner[g.away_team_abbr] = teams_by_abbr.get(g.away_team_abbr).id if teams_by_abbr.get(g.away_team_abbr) else None
                    abbr_to_winner[g.home_team_abbr] = teams_by_abbr.get(g.away_team_abbr).id if teams_by_abbr.get(g.away_team_abbr) else None

    # Count total distinct entries with a pick this week
    total_entries_q = select(func.count(func.distinct(Pick.entry_id))).where(Pick.week_id == week_id)
    total_count = int(db.execute(total_entries_q).scalar() or 0)

    # Determine losers by checking each pick against the known game winner for that team
    pick_rows = db.execute(select(Pick.entry_id, Pick.team_id).where(Pick.week_id == week_id)).all()
    losers_set = set()
    for entry_id, team_id in pick_rows:
        team = teams_by_id.get(team_id)
        if not team:
            continue
        # find the winner for the game this team appeared in
        winner_id = abbr_to_winner.get(team.abbreviation)
        if winner_id is None:
            # cannot determine yet (game not final or no mapping)
            continue
        if winner_id != team_id:
            losers_set.add(entry_id)

    losers_count = len(losers_set)

    resp["summary"] = {
        "total_entries": total_count,
        "losers": losers_count,
        "survivors": max(total_count - losers_count, 0),
    }

    return resp
