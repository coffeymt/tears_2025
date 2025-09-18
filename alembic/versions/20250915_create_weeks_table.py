"""create weeks table

Revision ID: 20250915_create_weeks_table
Revises: 
Create Date: 2025-09-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250915_create_weeks_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'weeks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('season_year', sa.Integer(), nullable=False, index=True),
        sa.Column('week_number', sa.Integer(), nullable=False, index=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('lock_time', sa.DateTime(), nullable=True),
        sa.Column('ineligible_teams', sa.JSON(), nullable=True),
        sa.Column('locked_games', sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_table('weeks')
