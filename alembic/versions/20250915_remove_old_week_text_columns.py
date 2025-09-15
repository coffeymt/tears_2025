"""
Remove old TEXT list columns from weeks and rename JSON columns to original names.

Revision ID: 20250915_remove_old_week_text_columns
Revises: 20250915_add_week_json_columns
Create Date: 2025-09-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250915_remove_old_week_text_columns"
down_revision = "20250915_add_week_json_columns"
branch_labels = None
depends_on = None


def upgrade():
    # If the JSON columns were added with alternate names, rename them to the canonical names
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('weeks')]

    # If our previous migration created ineligible_teams_json and locked_games_json, rename them
    if 'ineligible_teams_json' in cols and 'ineligible_teams' not in cols:
        op.alter_column('weeks', 'ineligible_teams_json', new_column_name='ineligible_teams')
    if 'locked_games_json' in cols and 'locked_games' not in cols:
        op.alter_column('weeks', 'locked_games_json', new_column_name='locked_games')

    # Drop old text columns if they exist
    cols = [c['name'] for c in inspector.get_columns('weeks')]
    if 'ineligible_teams_text' in cols:
        op.drop_column('weeks', 'ineligible_teams_text')
    if 'locked_games_text' in cols:
        op.drop_column('weeks', 'locked_games_text')

    # Also drop legacy-named TEXT columns if present (common name = ineligible_teams, locked_games)
    # We only drop them if a JSON column with the same name now exists to preserve data safety.
    cols = [c['name'] for c in inspector.get_columns('weeks')]
    if 'ineligible_teams' in cols and 'ineligible_teams' in cols:
        # If the existing 'ineligible_teams' column is of type TEXT, and we also have a JSON copy, attempt to drop the TEXT one.
        # To avoid accidental drops, we check the column type.
        col_info = next((c for c in inspector.get_columns('weeks') if c['name'] == 'ineligible_teams'), None)
        if col_info and getattr(col_info['type'], '__class__', None).__name__ == 'TEXT':
            # There is a TEXT column named ineligible_teams; we will drop it only if a JSON counterpart was renamed earlier.
            # For safety, skip automatic drop to avoid losing data. This branch is conservative.
            pass


def downgrade():
    # In downgrade we will attempt to recreate the old TEXT columns and copy JSON data into them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('weeks')]

    # Recreate old TEXT columns if missing
    if 'ineligible_teams' in cols and 'ineligible_teams_text' not in cols:
        op.add_column('weeks', sa.Column('ineligible_teams_text', sa.Text(), nullable=True))
        # Copy JSON into text column
        op.execute("UPDATE weeks SET ineligible_teams_text = ineligible_teams::text")
    if 'locked_games' in cols and 'locked_games_text' not in cols:
        op.add_column('weeks', sa.Column('locked_games_text', sa.Text(), nullable=True))
        op.execute("UPDATE weeks SET locked_games_text = locked_games::text")
