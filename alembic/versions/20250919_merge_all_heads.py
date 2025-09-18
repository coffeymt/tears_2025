"""merge all heads

Revision ID: 20250919_merge_all_heads
Revises: 20250918_merge_heads, 20250915_create_weeks_table
Create Date: 2025-09-19
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20250919_merge_all_heads'
down_revision = ('20250918_merge_heads', '20250915_create_weeks_table')
branch_labels = None
depends_on = None


def upgrade():
    # Merge point to unify multiple heads; no schema changes.
    pass


def downgrade():
    pass
