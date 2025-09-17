from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.game import Game
from app.models.pick import Pick
from app.models.entry import Entry
from app.models.week import Week
from app.models.team import Team


class FinalizeError(Exception):
    pass


def _apply_game_updates(db: Session, games_payload: list) -> None:
    """Apply final score updates to Game rows. Raises FinalizeError on validation failures."""
    for g in games_payload:
        game_id = g.get("game_id")
        if game_id is None:
            raise FinalizeError("game_id is required for each game")
        game = db.get(Game, game_id)
        if not game:
            raise FinalizeError(f"Game not found: {game_id}")
        # Expect explicit integer scores
        try:
            game.home_score = int(g.get("home_score", 0))
            game.away_score = int(g.get("away_score", 0))
        except (TypeError, ValueError):
            raise FinalizeError(f"Invalid scores for game {game_id}")
        # mark final
        setattr(game, "is_final", True)
        db.add(game)


def _compute_game_winner(db: Session, game: Game):
    """Return winning team id for a game or None for tie/unknown."""
    if game.home_score is None or game.away_score is None:
        return None
    if game.home_score > game.away_score:
        # lookup team by abbreviation
        team = db.query(Team).filter(Team.abbreviation == game.home_team_abbr).first()
        return team.id if team else None
    if game.away_score > game.home_score:
        team = db.query(Team).filter(Team.abbreviation == game.away_team_abbr).first()
        return team.id if team else None
    # tie
    return None


def finalize_week_scores(db: Session, week_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize games for a week and resolve picks.

    This function performs updates in a transaction: updates games, computes winning teams,
    updates picks.result to 'win'|'loss', and marks entries eliminated when they lose.
    """
    games_payload = payload.get("games") or []
    if not isinstance(games_payload, list):
        raise FinalizeError("'games' must be a list in payload")

    processed_picks = 0

    # Use a transaction scope; caller (router) does not manage transactions explicitly
    try:
        if db.in_transaction():
            tx = db.begin_nested()
        else:
            tx = db.begin()
        with tx:
            # Validate week exists
            week = db.get(Week, week_id)
            if not week:
                raise FinalizeError("Week not found")

            _apply_game_updates(db, games_payload)

            # Re-load updated games from DB and compute winners per game
            game_winners = {}
            for g in games_payload:
                gid = g.get("game_id")
                game = db.get(Game, gid)
                if not game:
                    raise FinalizeError(f"Game not found after update: {gid}")
                winner = _compute_game_winner(db, game)
                game_winners[gid] = winner

            # Query picks for the week
            picks = db.query(Pick).filter(Pick.week_id == week_id).all()
            for p in picks:
                # determine if the pick corresponds to a winning team in any game
                is_win = False
                for gid, winner in game_winners.items():
                    if winner is not None and winner == p.team_id:
                        is_win = True
                        break
                # update pick result only if changed
                new_result = "win" if is_win else "loss"
                if p.result != new_result:
                    p.result = new_result
                    db.add(p)
                processed_picks += 1

                if not is_win:
                    # mark the entry eliminated if not already
                    entry = db.get(Entry, p.entry_id)
                    if entry and not getattr(entry, "is_eliminated", False):
                        entry.is_eliminated = True
                        db.add(entry)

    except SQLAlchemyError as e:
        raise FinalizeError(str(e))

    return {"status": "ok", "processed_games": len(games_payload), "processed_picks": processed_picks}
