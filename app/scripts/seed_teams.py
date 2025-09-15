"""Idempotent seeder for canonical NFL teams.

This script exposes a `seed_teams(db)` function that inserts or upserts
the 32 NFL teams into the `teams` table. Tests call the function directly
against a temporary SQLite DB.
"""
from sqlalchemy import text

# Canonical teams data: abbreviation, name, city, conference, division
_TEAMS = [
    ("ARI", "Cardinals", "Arizona", "NFC", "West"),
    ("ATL", "Falcons", "Atlanta", "NFC", "South"),
    ("BAL", "Ravens", "Baltimore", "AFC", "North"),
    ("BUF", "Bills", "Buffalo", "AFC", "East"),
    ("CAR", "Panthers", "Carolina", "NFC", "South"),
    ("CHI", "Bears", "Chicago", "NFC", "North"),
    ("CIN", "Bengals", "Cincinnati", "AFC", "North"),
    ("CLE", "Browns", "Cleveland", "AFC", "North"),
    ("DAL", "Cowboys", "Dallas", "NFC", "East"),
    ("DEN", "Broncos", "Denver", "AFC", "West"),
    ("DET", "Lions", "Detroit", "NFC", "North"),
    ("GB", "Packers", "Green Bay", "NFC", "North"),
    ("HOU", "Texans", "Houston", "AFC", "South"),
    ("IND", "Colts", "Indianapolis", "AFC", "South"),
    ("JAX", "Jaguars", "Jacksonville", "AFC", "South"),
    ("KC", "Chiefs", "Kansas City", "AFC", "West"),
    ("LV", "Raiders", "Las Vegas", "AFC", "West"),
    ("LAC", "Chargers", "Los Angeles", "AFC", "West"),
    ("LAR", "Rams", "Los Angeles", "NFC", "West"),
    ("MIA", "Dolphins", "Miami", "AFC", "East"),
    ("MIN", "Vikings", "Minnesota", "NFC", "North"),
    ("NE", "Patriots", "New England", "AFC", "East"),
    ("NO", "Saints", "New Orleans", "NFC", "South"),
    ("NYG", "Giants", "New York", "NFC", "East"),
    ("NYJ", "Jets", "New York", "AFC", "East"),
    ("PHI", "Eagles", "Philadelphia", "NFC", "East"),
    ("PIT", "Steelers", "Pittsburgh", "AFC", "North"),
    ("SEA", "Seahawks", "Seattle", "NFC", "West"),
    ("SF", "49ers", "San Francisco", "NFC", "West"),
    ("TB", "Buccaneers", "Tampa Bay", "NFC", "South"),
    ("TEN", "Titans", "Tennessee", "AFC", "South"),
    ("WAS", "Commanders", "Washington", "NFC", "East"),
]


def seed_teams(db):
    """Idempotently insert or update the teams.

    db: a SQLAlchemy Connection or Session supporting execute(text(), params)
    """
    # Use simple UPSERT logic compatible with SQLite and Postgres
    for abbr, name, city, conference, division in _TEAMS:
        # Insert or replace by abbreviation
        sql = text(
            """
            INSERT INTO teams (abbreviation, name, city, conference, division)
            VALUES (:abbr, :name, :city, :conference, :division)
            ON CONFLICT(abbreviation) DO UPDATE SET
              name=excluded.name,
              city=excluded.city,
              conference=excluded.conference,
              division=excluded.division
            """
        )
        try:
            db.execute(sql, {"abbr": abbr, "name": name, "city": city, "conference": conference, "division": division})
        except Exception:
            # Fallback for SQLite without ON CONFLICT support in some builds: do a simple upsert emulation
            existing = db.execute(text("SELECT id FROM teams WHERE abbreviation = :abbr"), {"abbr": abbr}).fetchone()
            if existing:
                db.execute(text("UPDATE teams SET name=:name, city=:city, conference=:conference, division=:division WHERE abbreviation=:abbr"), {"abbr": abbr, "name": name, "city": city, "conference": conference, "division": division})
            else:
                db.execute(text("INSERT INTO teams (abbreviation, name, city, conference, division) VALUES (:abbr, :name, :city, :conference, :division)"), {"abbr": abbr, "name": name, "city": city, "conference": conference, "division": division})

    # commit if Session provided
    try:
        db.commit()
    except Exception:
        pass


if __name__ == "__main__":
    print("Run this script via import: call seed_teams(db)")
