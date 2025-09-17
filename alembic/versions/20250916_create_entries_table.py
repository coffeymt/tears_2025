"""create entries table

Revision ID: 20250916_create_entries_table
Revises: 20250915_create_games_table
Create Date: 2025-09-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250916_create_entries_table'
down_revision = '20250915_create_games_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('week_id', sa.Integer(), sa.ForeignKey('weeks.id'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('season_year', sa.Integer(), nullable=False),
        sa.Column('picks', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        # unique per user per season by name
        sa.UniqueConstraint('user_id', 'season_year', 'name', name='uq_entries_user_season_name'),
    )


def downgrade():
    op.drop_table('entries')
