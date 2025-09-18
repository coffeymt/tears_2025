"""create games table

Revision ID: 20250915_create_games_table
Revises: 
Create Date: 2025-09-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250915_create_games_table'
down_revision = '20250915_create_weeks_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('week_id', sa.Integer(), sa.ForeignKey('weeks.id'), nullable=False, index=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('home_team_abbr', sa.String(), nullable=False, index=True),
        sa.Column('away_team_abbr', sa.String(), nullable=False, index=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade():
    op.drop_table('games')
