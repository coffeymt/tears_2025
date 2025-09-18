"""add user contact fields
Revision ID: 5b284598fc9a
Revises: 20250920_add_team_fks
Create Date: 2025-09-17 22:55:53.370303
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5b284598fc9a'
down_revision = '20250920_add_team_fks'
branch_labels = None
depends_on = None


def upgrade():
    # Add contact/profile fields to users table
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.create_index('ix_users_phone_number', 'users', ['phone_number'], unique=False)


def downgrade():
    # Remove the added columns
    op.drop_index('ix_users_phone_number', table_name='users')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
