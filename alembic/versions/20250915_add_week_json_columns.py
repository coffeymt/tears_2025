"""
Add JSON columns for Week list fields and backfill from existing TEXT columns.

Revision ID: 20250915_add_week_json_columns
Revises: 20250915_seed_32_teams
Create Date: 2025-09-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

# revision identifiers, used by Alembic.
revision = "20250915_add_week_json_columns"
down_revision = "20250915_seed_32_teams"
branch_labels = None
depends_on = None


def upgrade():
    # Add new JSON columns (nullable by default)
    op.add_column('weeks', sa.Column('ineligible_teams_json', sa.JSON(), nullable=True))
    op.add_column('weeks', sa.Column('locked_games_json', sa.JSON(), nullable=True))

    bind = op.get_bind()
    # Backfill existing data from text columns if they exist
    # Use a conservative approach: try to SELECT the text columns, if not present skip
    inspector = sa.inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('weeks')]
    if 'ineligible_teams' in cols or 'locked_games' in cols:
        # Select rows with the old text columns and parse them safely
        select_sql = text('SELECT id, ineligible_teams, locked_games FROM weeks')
        result = bind.execute(select_sql)
        rows = result.fetchall()
        for row in rows:
            wk_id = row[0]
            i_text = row[1]
            l_text = row[2]
            try:
                i_val = json.loads(i_text) if i_text else []
            except Exception:
                i_val = []
            try:
                l_val = json.loads(l_text) if l_text else []
            except Exception:
                l_val = []
            # Update the row using parameter binding
            update_sql = text('UPDATE weeks SET ineligible_teams_json = :i_val, locked_games_json = :l_val WHERE id = :id')
            bind.execute(update_sql, {"i_val": i_val, "l_val": l_val, "id": wk_id})


def downgrade():
    # Drop the JSON columns
    op.drop_column('weeks', 'locked_games_json')
    op.drop_column('weeks', 'ineligible_teams_json')
