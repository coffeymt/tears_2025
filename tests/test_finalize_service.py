import sys
import os
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    """Set a unique DATABASE_URL per test to avoid locking and collisions."""
    db_file = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    yield
    os.environ.pop("DATABASE_URL", None)

from app.services.finalize import finalize_week_scores, FinalizeError
from app.models.week import Week
from app.models.game import Game
from app.models.team import Team
import uuid
from datetime import datetime
import app.models.user
import app.models.entry
import app.models.pick
import app.models.password_reset
import app.models.game
import app.models.week
import app.models.team
from app.models.entry import Entry
from app.models.pick import Pick
from app.models.base import Base
from app.db import engine, SessionLocal
from sqlalchemy.orm import Session


def _create_week_and_game(db: Session):
    week = Week(season_year=2025, week_number=1)
    db.add(week)
    db.commit()
    db.refresh(week)
    team_a = Team(abbreviation=f"AAA{uuid.uuid4().hex[:6]}", name="Team A")
    team_b = Team(abbreviation=f"BBB{uuid.uuid4().hex[:6]}", name="Team B")
    db.add_all([team_a, team_b])
    db.commit()
    db.refresh(team_a)
    db.refresh(team_b)
    game = Game(week_id=week.id, start_time=datetime(2025,9,1,12,0,0), home_team_abbr=team_a.abbreviation, away_team_abbr=team_b.abbreviation)
    db.add(game)
    db.commit()
    db.refresh(game)
    return week, game, team_a, team_b


def test_finalize_marks_winner_and_eliminates(tmp_path, monkeypatch):
    db: Session = SessionLocal()
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    week, game, team_a, team_b = _create_week_and_game(db)

    # Create entries and picks
    import uuid as _uuid
    entry1 = Entry(user_id=1, week_id=week.id, name=f"e1-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    entry2 = Entry(user_id=2, week_id=week.id, name=f"e2-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add_all([entry1, entry2])
    db.commit()
    db.refresh(entry1)
    db.refresh(entry2)

    pick1 = Pick(entry_id=entry1.id, week_id=week.id, team_id=team_a.id)
    pick2 = Pick(entry_id=entry2.id, week_id=week.id, team_id=team_b.id)
    db.add_all([pick1, pick2])
    db.commit()

    payload = {"games": [{"game_id": game.id, "home_score": 21, "away_score": 14}]}
    result = finalize_week_scores(db, week.id, payload)
    assert result["status"] == "ok"

    # reload picks and entries
    p1 = db.get(Pick, pick1.id)
    p2 = db.get(Pick, pick2.id)
    assert p1.result == "win"
    assert p2.result == "loss"

    e1 = db.get(Entry, entry1.id)
    e2 = db.get(Entry, entry2.id)
    assert getattr(e1, "is_eliminated", False) == False
    assert getattr(e2, "is_eliminated", False) == True


def test_finalize_handles_tie_as_loss(tmp_path):
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"e-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()

    payload = {"games": [{"game_id": game.id, "home_score": 14, "away_score": 14}]}
    result = finalize_week_scores(db, week.id, payload)
    assert result["status"] == "ok"

    p = db.get(Pick, pick.id)
    assert p.result == "loss"
    e = db.get(Entry, entry.id)
    assert getattr(e, "is_eliminated", False) == True


def test_finalize_transaction_rolls_back(tmp_path, monkeypatch):
    # Setup initial data in one session
    s1: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(s1)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"rb-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    s1.add(entry)
    s1.commit()
    s1.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    s1.add(pick)
    s1.commit()
    # Capture ids before closing session to avoid detached-instance refresh errors
    week_id = week.id
    game_id = game.id
    pick_id = pick.id
    s1.close()

    # Use a fresh session for the finalize call so rollback visibility can be tested
    s2: Session = SessionLocal()

    # Prepare payload
    payload = {"games": [{"game_id": game_id, "home_score": 21, "away_score": 14}]}

    # Monkeypatch the winner computation to raise an error, simulating a failure after game updates
    from app.services import finalize as finalize_mod

    def _fail_compute(*args, **kwargs):
        raise finalize_mod.FinalizeError("simulated failure to trigger rollback")

    monkeypatch.setattr(finalize_mod, "_compute_game_winner", _fail_compute)

    import pytest
    with pytest.raises(finalize_mod.FinalizeError):
        finalize_week_scores(s2, week_id, payload)
    s2.close()

    # New session to verify DB state — game should NOT be marked final due to rollback
    s3: Session = SessionLocal()
    g = s3.get(Game, game_id)
    assert not getattr(g, "is_final", False)
    # scores should not be persisted
    assert g.home_score is None and g.away_score is None
    s3.close()


def test_finalize_payload_validation(tmp_path):
    """Payload must include 'games' as a list — invalid payloads raise FinalizeError and no DB changes occur."""
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"pv-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()

    # The service treats missing or null 'games' as an empty list (allowed)
    from app.services import finalize as finalize_mod
    import pytest

    ok_payloads = [{}, {"games": None}]
    for payload in ok_payloads:
        res = finalize_week_scores(db, week.id, payload)
        assert res["status"] == "ok"
        assert res["processed_games"] == 0

    # Non-list 'games' (e.g., a string) should raise
    with pytest.raises(finalize_mod.FinalizeError):
        finalize_week_scores(db, week.id, {"games": "not-a-list"})

    # Ensure DB unchanged (game still not final)
    g = db.get(Game, game.id)
    assert not getattr(g, "is_final", False)


def test_finalize_pick_references_nonparticipating_team(tmp_path):
    """If a pick references a team not participating in any finalized game, it should be treated as loss (no crash)."""
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    # Create an unrelated team that doesn't play in the game
    other = Team(abbreviation=f"ZZZ{uuid.uuid4().hex[:4]}", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"nt-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Pick references 'other' team which did not play in the created game
    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=other.id)
    db.add(pick)
    db.commit()

    payload = {"games": [{"game_id": game.id, "home_score": 21, "away_score": 14}]}
    result = finalize_week_scores(db, week.id, payload)
    assert result["status"] == "ok"

    # The pick should be marked loss because team didn't win any game
    p = db.get(Pick, pick.id)
    assert p.result == "loss"


def test_finalize_idempotence(tmp_path):
    """Calling finalize twice with the same payload should be safe and idempotent."""
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"id-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()

    payload = {"games": [{"game_id": game.id, "home_score": 21, "away_score": 14}]}

    # First finalize: should mark pick as win
    r1 = finalize_week_scores(db, week.id, payload)
    assert r1["status"] == "ok"
    p1 = db.get(Pick, pick.id)
    assert p1.result == "win"

    # Second finalize: should not change the result or error
    r2 = finalize_week_scores(db, week.id, payload)
    assert r2["status"] == "ok"
    p2 = db.get(Pick, pick.id)
    assert p2.result == "win"


def test_finalize_missing_game_id_raises(tmp_path):
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"mg-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()

    # Refer to a non-existent game id
    bad_game_id = game.id + 99999
    payload = {"games": [{"game_id": bad_game_id, "home_score": 21, "away_score": 14}]}
    from app.services import finalize as finalize_mod
    import pytest
    with pytest.raises(finalize_mod.FinalizeError):
        finalize_week_scores(db, week.id, payload)

    # Ensure DB unchanged (original game still not final)
    g = db.get(Game, game.id)
    assert not getattr(g, "is_final", False)


def test_finalize_unknown_team_id_treated_as_loss(tmp_path):
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"ut-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Use a team id that does not exist
    unknown_team_id = 9999999
    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=unknown_team_id)
    db.add(pick)
    db.commit()

    payload = {"games": [{"game_id": game.id, "home_score": 21, "away_score": 14}]}
    res = finalize_week_scores(db, week.id, payload)
    assert res["status"] == "ok"

    p = db.get(Pick, pick.id)
    # unknown team id should be treated as loss (since not equal to computed winner)
    assert p.result == "loss"


def test_finalize_nested_transaction_behaves(tmp_path, monkeypatch):
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)
    week, game, team_a, team_b = _create_week_and_game(db)

    import uuid as _uuid
    entry = Entry(user_id=1, week_id=week.id, name=f"ntb-{_uuid.uuid4().hex[:6]}", season_year=week.season_year, picks=[])
    db.add(entry)
    db.commit()
    db.refresh(entry)

    pick = Pick(entry_id=entry.id, week_id=week.id, team_id=team_a.id)
    db.add(pick)
    db.commit()

    payload = {"games": [{"game_id": game.id, "home_score": 21, "away_score": 14}]}

    # Start an outer transaction on a fresh session and force finalize to fail to ensure nested rollback
    s_outer = SessionLocal()
    try:
        from app.services import finalize as finalize_mod

        def _fail(*args, **kwargs):
            raise finalize_mod.FinalizeError("forced")

        monkeypatch.setattr(finalize_mod, "_compute_game_winner", _fail)
        import pytest
        with s_outer.begin():
            with pytest.raises(finalize_mod.FinalizeError):
                finalize_week_scores(s_outer, week.id, payload)
        # after exiting outer transaction context, ensure nothing persisted
    finally:
        s_outer.close()

    # Ensure no changes were persisted
    check_db = SessionLocal()
    g = check_db.get(Game, game.id)
    assert not getattr(g, "is_final", False)
    check_db.close()


def test_finalize_large_batch_sanity(tmp_path):
    db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # Create teams and games
    NUM = 30
    teams = []
    for i in range(NUM * 2):
        t = Team(abbreviation=f"T{i}{uuid.uuid4().hex[:3]}", name=f"Team{i}")
        db.add(t)
        teams.append(t)
    db.commit()
    for t in teams:
        db.refresh(t)

    week = Week(season_year=2025, week_number=99)
    db.add(week)
    db.commit()
    db.refresh(week)

    games = []
    for i in range(NUM):
        home = teams[i * 2]
        away = teams[i * 2 + 1]
        g = Game(week_id=week.id, start_time=datetime(2025,9,1,12,0,0), home_team_abbr=home.abbreviation, away_team_abbr=away.abbreviation)
        db.add(g)
        games.append(g)
    db.commit()
    for g in games:
        db.refresh(g)

    # Create entries and one pick per entry (schema enforces unique entry/week)
    import random
    ENTRIES = 120
    total_picks = 0
    for i in range(ENTRIES):
        e = Entry(user_id=1000 + i, week_id=week.id, name=f"b-{i}-{uuid.uuid4().hex[:4]}", season_year=week.season_year, picks=[])
        db.add(e)
        db.commit()
        db.refresh(e)
        # pick a random game's home team for this entry
        g = random.choice(games)
        team_id = db.query(Team).filter(Team.abbreviation == g.home_team_abbr).first().id
        p = Pick(entry_id=e.id, week_id=week.id, team_id=team_id)
        db.add(p)
        total_picks += 1
        db.commit()

    # Build payload: home team wins for all games
    payload = {"games": [{"game_id": g.id, "home_score": 21, "away_score": 14} for g in games]}
    res = finalize_week_scores(db, week.id, payload)
    assert res["status"] == "ok"
    assert res["processed_picks"] == total_picks
