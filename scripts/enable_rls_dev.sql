-- Safe dev script to enable Row Level Security (RLS) and create owner/admin policies
-- Run this in dev only. Review policies before applying in production.

BEGIN;

-- entries: owner-only access
ALTER TABLE IF EXISTS public.entries ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.entries FROM public;
DROP POLICY IF EXISTS entries_owner_policy ON public.entries;
CREATE POLICY entries_owner_policy
  ON public.entries
  FOR ALL
  USING (user_id::text = auth.uid()::text)
  WITH CHECK (user_id::text = auth.uid()::text);

-- picks: restrict to owner via entries (assuming entries.user_id)
ALTER TABLE IF EXISTS public.picks ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.picks FROM public;
DROP POLICY IF EXISTS picks_owner_via_entry ON public.picks;
CREATE POLICY picks_owner_via_entry
  ON public.picks
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.entries e
      WHERE e.id = public.picks.entry_id AND e.user_id::text = auth.uid()::text
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.entries e
      WHERE e.id = public.picks.entry_id AND e.user_id::text = auth.uid()::text
    )
  );

-- users: owner can access own profile
ALTER TABLE IF EXISTS public.users ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.users FROM public;
DROP POLICY IF EXISTS users_owner_policy ON public.users;
CREATE POLICY users_owner_policy
  ON public.users
  FOR ALL
  USING (id::text = auth.uid()::text)
  WITH CHECK (id::text = auth.uid()::text);

-- teams / games / weeks: public read, admin-only writes
ALTER TABLE IF EXISTS public.teams ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS teams_public_select ON public.teams;
CREATE POLICY teams_public_select ON public.teams FOR SELECT USING (true);
DROP POLICY IF EXISTS teams_admin_writes_insert ON public.teams;
DROP POLICY IF EXISTS teams_admin_writes_update ON public.teams;
DROP POLICY IF EXISTS teams_admin_writes_delete ON public.teams;
CREATE POLICY teams_admin_writes_insert ON public.teams FOR INSERT
  WITH CHECK (current_setting('request.jwt.claims.is_admin', true) = 'true');
CREATE POLICY teams_admin_writes_update ON public.teams FOR UPDATE
  USING (current_setting('request.jwt.claims.is_admin', true) = 'true')
  WITH CHECK (current_setting('request.jwt.claims.is_admin', true) = 'true');
CREATE POLICY teams_admin_writes_delete ON public.teams FOR DELETE
  USING (current_setting('request.jwt.claims.is_admin', true) = 'true');

ALTER TABLE IF EXISTS public.games ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS games_public_select ON public.games;
CREATE POLICY games_public_select ON public.games FOR SELECT USING (true);
DROP POLICY IF EXISTS games_admin_writes_insert ON public.games;
DROP POLICY IF EXISTS games_admin_writes_update ON public.games;
DROP POLICY IF EXISTS games_admin_writes_delete ON public.games;
CREATE POLICY games_admin_writes_insert ON public.games FOR INSERT
  WITH CHECK (current_setting('request.jwt.claims.is_admin', true) = 'true');
CREATE POLICY games_admin_writes_update ON public.games FOR UPDATE
  USING (current_setting('request.jwt.claims.is_admin', true) = 'true')
  WITH CHECK (current_setting('request.jwt.claims.is_admin', true) = 'true');
CREATE POLICY games_admin_writes_delete ON public.games FOR DELETE
  USING (current_setting('request.jwt.claims.is_admin', true) = 'true');

ALTER TABLE IF EXISTS public.weeks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS weeks_public_select ON public.weeks;
CREATE POLICY weeks_public_select ON public.weeks FOR SELECT USING (true);
DROP POLICY IF EXISTS weeks_admin_writes_insert ON public.weeks;
DROP POLICY IF EXISTS weeks_admin_writes_update ON public.weeks;
DROP POLICY IF EXISTS weeks_admin_writes_delete ON public.weeks;
CREATE POLICY weeks_admin_writes_insert ON public.weeks FOR INSERT
  WITH CHECK (current_setting('request.jwt.claims.is_admin', true) = 'true');
CREATE POLICY weeks_admin_writes_update ON public.weeks FOR UPDATE
  USING (current_setting('request.jwt.claims.is_admin', true) = 'true')
  WITH CHECK (current_setting('request.jwt.claims.is_admin', true) = 'true');
CREATE POLICY weeks_admin_writes_delete ON public.weeks FOR DELETE
  USING (current_setting('request.jwt.claims.is_admin', true) = 'true');

-- sensitive internal table: revoke public access
REVOKE ALL ON public.alembic_version FROM public;

COMMIT;

-- NOTE: Do not enable CONCURRENT index creation inside a transaction. Production index creation should use
-- scripts/create_indexes_concurrent.sql executed via psql (outside transactions).
