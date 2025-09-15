"""seed 32 NFL teams

Revision ID: seed_32_teams_20250915
Revises: 
Create Date: 2025-09-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'seed_32_teams_20250915'
down_revision = None
branch_labels = None
depends_on = None


def _teams_list():
    return [
        {"abbreviation": "ARI", "name": "Cardinals", "city": "Arizona", "conference": "NFC", "division": "West"},
        {"abbreviation": "ATL", "name": "Falcons", "city": "Atlanta", "conference": "NFC", "division": "South"},
        {"abbreviation": "BAL", "name": "Ravens", "city": "Baltimore", "conference": "AFC", "division": "North"},
        {"abbreviation": "BUF", "name": "Bills", "city": "Buffalo", "conference": "AFC", "division": "East"},
        {"abbreviation": "CAR", "name": "Panthers", "city": "Carolina", "conference": "NFC", "division": "South"},
        {"abbreviation": "CHI", "name": "Bears", "city": "Chicago", "conference": "NFC", "division": "North"},
        {"abbreviation": "CIN", "name": "Bengals", "city": "Cincinnati", "conference": "AFC", "division": "North"},
        {"abbreviation": "CLE", "name": "Browns", "city": "Cleveland", "conference": "AFC", "division": "North"},
        {"abbreviation": "DAL", "name": "Cowboys", "city": "Dallas", "conference": "NFC", "division": "East"},
        {"abbreviation": "DEN", "name": "Broncos", "city": "Denver", "conference": "AFC", "division": "West"},
        {"abbreviation": "DET", "name": "Lions", "city": "Detroit", "conference": "NFC", "division": "North"},
        {"abbreviation": "GB",  "name": "Packers", "city": "Green Bay", "conference": "NFC", "division": "North"},
        {"abbreviation": "HOU", "name": "Texans", "city": "Houston", "conference": "AFC", "division": "South"},
        {"abbreviation": "IND", "name": "Colts", "city": "Indianapolis", "conference": "AFC", "division": "South"},
        {"abbreviation": "JAX", "name": "Jaguars", "city": "Jacksonville", "conference": "AFC", "division": "South"},
        {"abbreviation": "KC",  "name": "Chiefs", "city": "Kansas City", "conference": "AFC", "division": "West"},
        {"abbreviation": "LAC", "name": "Chargers", "city": "Los Angeles", "conference": "AFC", "division": "West"},
        {"abbreviation": "LAR", "name": "Rams", "city": "Los Angeles", "conference": "NFC", "division": "West"},
        {"abbreviation": "LV",  "name": "Raiders", "city": "Las Vegas", "conference": "AFC", "division": "West"},
        {"abbreviation": "MIA", "name": "Dolphins", "city": "Miami", "conference": "AFC", "division": "East"},
        {"abbreviation": "MIN", "name": "Vikings", "city": "Minnesota", "conference": "NFC", "division": "North"},
        {"abbreviation": "NE",  "name": "Patriots", "city": "New England", "conference": "AFC", "division": "East"},
        {"abbreviation": "NO",  "name": "Saints", "city": "New Orleans", "conference": "NFC", "division": "South"},
        {"abbreviation": "NYG", "name": "Giants", "city": "New York", "conference": "NFC", "division": "East"},
        {"abbreviation": "NYJ", "name": "Jets", "city": "New York", "conference": "AFC", "division": "East"},
        {"abbreviation": "PHI", "name": "Eagles", "city": "Philadelphia", "conference": "NFC", "division": "East"},
        {"abbreviation": "PIT", "name": "Steelers", "city": "Pittsburgh", "conference": "AFC", "division": "North"},
        {"abbreviation": "SEA", "name": "Seahawks", "city": "Seattle", "conference": "NFC", "division": "West"},
        {"abbreviation": "SF",  "name": "49ers", "city": "San Francisco", "conference": "NFC", "division": "West"},
        {"abbreviation": "TB",  "name": "Buccaneers", "city": "Tampa Bay", "conference": "NFC", "division": "South"},
        {"abbreviation": "TEN", "name": "Titans", "city": "Tennessee", "conference": "AFC", "division": "South"},
        {"abbreviation": "WAS", "name": "Commanders", "city": "Washington", "conference": "NFC", "division": "East"},
    ]


def upgrade():
    conn = op.get_bind()
    teams = _teams_list()
    for t in teams:
        # Check existence by abbreviation and insert if missing (dialect-agnostic)
        exists = conn.execute(sa.text("SELECT 1 FROM teams WHERE abbreviation = :abbr"), {"abbr": t["abbreviation"]}).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO teams (abbreviation, name, city, conference, division) VALUES (:abbreviation, :name, :city, :conference, :division)"
                ),
                t,
            )


def downgrade():
    conn = op.get_bind()
    teams = _teams_list()
    for t in teams:
        conn.execute(sa.text("DELETE FROM teams WHERE abbreviation = :abbr"), {"abbr": t["abbreviation"]})
