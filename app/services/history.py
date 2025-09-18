from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.week import Week
from app.models.entry import Entry
from app.models.pick import Pick
from sqlalchemy import select
from typing import Tuple


def get_history_matrix(db: Session, season_year: int = None) -> Dict:
    """Return a dict matching HistoryMatrixResponse: {weeks: [week_numbers], entries: [{entry_id, entry_name, picks: [...]}, ...]}"""

    # Fetch weeks ordered by season_year, week_number. Optionally filter by season_year
    q = db.query(Week)
    if season_year is not None:
        q = q.filter(Week.season_year == season_year)
    weeks = q.order_by(Week.season_year, Week.week_number).all()
    week_ids = [w.id for w in weeks]
    week_numbers = [w.week_number for w in weeks]

    # Map week id to its position index
    week_index = {wid: idx for idx, wid in enumerate(week_ids)}

    # Fetch entries for the season (if season_year supplied, use it; otherwise include all)
    eq = db.query(Entry)
    if season_year is not None:
        eq = eq.filter(Entry.season_year == season_year)
    entries = eq.order_by(Entry.id).all()

    # Pre-build entry rows with empty picks list sized to weeks
    entry_rows = {}
    for e in entries:
        entry_rows[e.id] = {
            "entry_id": e.id,
            "entry_name": e.name,
            "picks": [None] * len(week_ids),
        }

    if week_ids and entries:
        # Fetch all picks for those entries and weeks in a single query
        picks = (
            db.query(Pick)
            .filter(Pick.week_id.in_(week_ids))
            .filter(Pick.entry_id.in_(list(entry_rows.keys())))
            .all()
        )

        for p in picks:
            e_row = entry_rows.get(p.entry_id)
            if e_row is None:
                continue
            idx = week_index.get(p.week_id)
            if idx is None:
                continue
            e_row["picks"][idx] = p.team_id

    return {"weeks": week_numbers, "entries": list(entry_rows.values())}


def get_raw_matrix_records(db: Session, season_year: int = None) -> List[Tuple[int, str, int, int]]:
    """Return a flat list of records (entry_id, entry_name, week_number, team_id) by joining entries, picks, and weeks.

    This is the raw data (one row per pick) used to build the matrix. season_year optionally filters the rows.
    """
    # Build query using SQLAlchemy ORM-select
    stmt = (
        select(Entry.id, Entry.name, Week.week_number, Pick.team_id)
        .join(Pick, Pick.entry_id == Entry.id)
        .join(Week, Week.id == Pick.week_id)
    )
    if season_year is not None:
        stmt = stmt.where(Entry.season_year == season_year)
    # Order by entry id then week number to give a predictable flat result
    stmt = stmt.order_by(Entry.id, Week.week_number)
    results = db.execute(stmt).all()
    # results are list of Row tuples; convert to simple tuple list
    return [(r[0], r[1], r[2], r[3]) for r in results]
