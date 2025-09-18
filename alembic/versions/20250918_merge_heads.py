"""merge heads

Revision ID: 20250918_merge_heads
Revises: 20250915_remove_old_week_text_columns, 20250917_add_entry_is_paid
Create Date: 2025-09-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250918_merge_heads'
down_revision = ('20250915_remove_old_week_text_columns', '20250917_add_entry_is_paid')
branch_labels = None
depends_on = None


def upgrade():
    # This migration merges two heads; there are no schema changes — it simply records a merge point.
    pass


def downgrade():
    # No-op; can't reliably un-merge
    pass
