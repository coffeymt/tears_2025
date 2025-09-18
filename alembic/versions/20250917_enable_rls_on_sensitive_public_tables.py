"""enable rls on sensitive public tables
Revision ID: 20250917_enable_rls
Revises: 5b284598fc9a
Create Date: 2025-09-17 23:30:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250917_enable_rls'
down_revision = '5b284598fc9a'
branch_labels = None
depends_on = None


def upgrade():
    # Enable RLS on password_reset_tokens and alembic_version and create restrictive policies
    conn = op.get_bind()
    # Enable RLS
    conn.execute(sa.text("ALTER TABLE public.password_reset_tokens ENABLE ROW LEVEL SECURITY;"))
    conn.execute(sa.text("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;"))

    # Create deny-all policies to ensure RLS is enabled while preventing any non-privileged access.
    # This satisfies Supabase linter requirements while leaving access only to roles that bypass RLS (superuser/service roles).
    conn.execute(sa.text(
        """
        CREATE POLICY p_rpt_deny_all ON public.password_reset_tokens
            USING (false)
            WITH CHECK (false);
        """
    ))

    conn.execute(sa.text(
        """
        CREATE POLICY p_alembic_deny_all ON public.alembic_version
            USING (false)
            WITH CHECK (false);
        """
    ))


def downgrade():
    conn = op.get_bind()
    # Drop policies if they exist and disable RLS
    conn.execute(sa.text("DROP POLICY IF EXISTS p_rpt_deny_all ON public.password_reset_tokens;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS p_alembic_deny_all ON public.alembic_version;"))
    conn.execute(sa.text("ALTER TABLE public.password_reset_tokens DISABLE ROW LEVEL SECURITY;"))
    conn.execute(sa.text("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY;"))
