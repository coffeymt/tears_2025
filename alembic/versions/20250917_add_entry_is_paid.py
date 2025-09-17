"""add is_paid to entries

Revision ID: 20250917_add_entry_is_paid
Revises: 20250916_create_picks_table
Create Date: 2025-09-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250917_add_entry_is_paid'
down_revision = '20250916_create_picks_table'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('entries', sa.Column('is_paid', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    # Remove server_default to match SQLAlchemy model defaults where appropriate
    with op.get_context().autocommit_block():
        op.alter_column('entries', 'is_paid', server_default=None)


def downgrade():
    op.drop_column('entries', 'is_paid')
