"""create picks table

Revision ID: 20250916_create_picks_table
Revises: 20250916_create_entries_table
Create Date: 2025-09-16 00:05:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250916_create_picks_table'
down_revision = '20250916_create_entries_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'picks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('entries.id'), nullable=False, index=True),
        sa.Column('week_id', sa.Integer(), sa.ForeignKey('weeks.id'), nullable=False, index=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False, index=True),
        sa.Column('result', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('entry_id', 'week_id', name='uq_picks_entry_week'),
    )


def downgrade():
    op.drop_table('picks')
