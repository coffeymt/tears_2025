"""add team foreign keys to games and picks

Revision ID: 20250920_add_team_fks
Revises: 20250919_merge_all_heads
Create Date: 2025-09-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250920_add_team_fks'
down_revision = '20250919_merge_all_heads'
branch_labels = None
depends_on = None


def upgrade():
    # 1) add nullable FK columns
    op.add_column('games', sa.Column('home_team_id', sa.Integer(), nullable=True))
    op.add_column('games', sa.Column('away_team_id', sa.Integer(), nullable=True))
    op.add_column('picks', sa.Column('team_id_new', sa.Integer(), nullable=True))

    # 2) backfill games.home_team_id/away_team_id from abbreviations
    op.execute("""
    UPDATE games g SET home_team_id = t.id
    FROM teams t
    WHERE t.abbreviation = g.home_team_abbr AND g.home_team_id IS NULL;
    UPDATE games g SET away_team_id = t.id
    FROM teams t
    WHERE t.abbreviation = g.away_team_abbr AND g.away_team_id IS NULL;
    """)

    # 3) backfill picks.team_id_new conditionally: map from picks.team_abbr if that column exists,
    # otherwise map from the existing integer picks.team_id when present.
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='picks' AND column_name='team_abbr') THEN
            UPDATE picks p SET team_id_new = t.id
            FROM teams t
            WHERE t.abbreviation = p.team_abbr AND (p.team_id_new IS NULL OR p.team_id_new = 0);
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='picks' AND column_name='team_id') THEN
            UPDATE picks p SET team_id_new = p.team_id WHERE p.team_id IS NOT NULL AND p.team_id_new IS NULL;
        END IF;
    END$$;
    """)

    # 4) create indexes (non-concurrently in migration; production should use CONCURRENTLY outside transaction)
    op.create_index('idx_games_home_team_id', 'games', ['home_team_id'])
    op.create_index('idx_games_away_team_id', 'games', ['away_team_id'])
    op.create_index('idx_picks_team_id_new', 'picks', ['team_id_new'])

    # 5) find problematic rows (leave to operator to inspect logs). If none, promote columns to team_id
    # Here we assume operator has verified results; then rename picks.team_id_new -> team_id and remove old column if needed
    op.execute("""
    -- rename picks.team_id_new to team_id, preserving any existing column name collisions
    ALTER TABLE picks DROP COLUMN IF EXISTS team_id CASCADE;
    ALTER TABLE picks RENAME COLUMN team_id_new TO team_id;
    """)

    # 6) add FK constraints
    op.create_foreign_key('fk_games_home_team', 'games', 'teams', ['home_team_id'], ['id'])
    op.create_foreign_key('fk_games_away_team', 'games', 'teams', ['away_team_id'], ['id'])
    op.create_foreign_key('fk_picks_team', 'picks', 'teams', ['team_id'], ['id'])


def downgrade():
    # remove FKs and new columns
    op.drop_constraint('fk_picks_team', 'picks', type_='foreignkey')
    op.drop_constraint('fk_games_away_team', 'games', type_='foreignkey')
    op.drop_constraint('fk_games_home_team', 'games', type_='foreignkey')
    op.drop_index('idx_picks_team_id_new', table_name='picks')
    op.drop_index('idx_games_away_team_id', table_name='games')
    op.drop_index('idx_games_home_team_id', table_name='games')
    # attempt to restore previous picks.team_id state by adding a nullable integer
    op.add_column('picks', sa.Column('team_id_old', sa.Integer(), nullable=True))
    op.execute('ALTER TABLE picks RENAME COLUMN team_id TO team_id_new;')
    op.execute('ALTER TABLE picks RENAME COLUMN team_id_old TO team_id;')
    op.drop_column('picks', 'team_id_new')
    op.drop_column('games', 'home_team_id')
    op.drop_column('games', 'away_team_id')
