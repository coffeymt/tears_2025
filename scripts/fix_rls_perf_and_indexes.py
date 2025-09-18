"""Fix RLS policy performance issues and remove duplicate indexes.

This script:
- updates RLS policies to call auth/current_setting via SELECT once per statement
- drops duplicate indexes on `picks` using CONCURRENTLY (autocommit)
- prints verification details

Run with: $env:DATABASE_URL='postgresql://...'; python .\scripts\fix_rls_perf_and_indexes.py
"""
import os
import psycopg2


def parse_and_connect(database_url: str):
    # robust connect like other scripts to handle special chars
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        prefix, at, host_part = database_url.rpartition('@')
        scheme_and_auth = prefix
        if '://' in scheme_and_auth:
            scheme, _, auth = scheme_and_auth.partition('://')
        else:
            auth = scheme_and_auth

        if ':' in auth:
            user, _, password = auth.partition(':')
        else:
            user = auth
            password = None

        host_and_port, _, dbname = host_part.partition('/')
        if ':' in host_and_port:
            host, _, port = host_and_port.partition(':')
        else:
            host = host_and_port
            port = None

        conn_params = {}
        if dbname:
            conn_params['dbname'] = dbname
        if user:
            conn_params['user'] = user
        if password:
            conn_params['password'] = password
        if host:
            conn_params['host'] = host
        if port:
            try:
                conn_params['port'] = int(port)
            except Exception:
                conn_params['port'] = port

        try:
            return psycopg2.connect(**conn_params)
        except Exception:
            return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(database_url)


POLICY_SQL = r"""
-- entries
DROP POLICY IF EXISTS entries_owner_policy ON public.entries;
CREATE POLICY entries_owner_policy ON public.entries FOR ALL
  USING (user_id::text = (SELECT auth.uid())::text)
  WITH CHECK (user_id::text = (SELECT auth.uid())::text);

-- picks (ownership via entries)
DROP POLICY IF EXISTS picks_owner_via_entry ON public.picks;
CREATE POLICY picks_owner_via_entry ON public.picks FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.entries e
      WHERE e.id = public.picks.entry_id AND e.user_id::text = (SELECT auth.uid())::text
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.entries e
      WHERE e.id = public.picks.entry_id AND e.user_id::text = (SELECT auth.uid())::text
    )
  );

-- users
DROP POLICY IF EXISTS users_owner_policy ON public.users;
CREATE POLICY users_owner_policy ON public.users FOR ALL
  USING (id::text = (SELECT auth.uid())::text)
  WITH CHECK (id::text = (SELECT auth.uid())::text);

-- teams: public read, admin writes
DROP POLICY IF EXISTS teams_admin_writes_insert ON public.teams;
DROP POLICY IF EXISTS teams_admin_writes_update ON public.teams;
DROP POLICY IF EXISTS teams_admin_writes_delete ON public.teams;
CREATE POLICY teams_admin_writes_insert ON public.teams FOR INSERT
  WITH CHECK ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
CREATE POLICY teams_admin_writes_update ON public.teams FOR UPDATE
  USING ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true')
  WITH CHECK ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
CREATE POLICY teams_admin_writes_delete ON public.teams FOR DELETE
  USING ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');

-- games
DROP POLICY IF EXISTS games_admin_writes_insert ON public.games;
DROP POLICY IF EXISTS games_admin_writes_update ON public.games;
DROP POLICY IF EXISTS games_admin_writes_delete ON public.games;
CREATE POLICY games_admin_writes_insert ON public.games FOR INSERT
  WITH CHECK ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
CREATE POLICY games_admin_writes_update ON public.games FOR UPDATE
  USING ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true')
  WITH CHECK ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
CREATE POLICY games_admin_writes_delete ON public.games FOR DELETE
  USING ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');

-- weeks
DROP POLICY IF EXISTS weeks_admin_writes_insert ON public.weeks;
DROP POLICY IF EXISTS weeks_admin_writes_update ON public.weeks;
DROP POLICY IF EXISTS weeks_admin_writes_delete ON public.weeks;
CREATE POLICY weeks_admin_writes_insert ON public.weeks FOR INSERT
  WITH CHECK ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
CREATE POLICY weeks_admin_writes_update ON public.weeks FOR UPDATE
  USING ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true')
  WITH CHECK ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
CREATE POLICY weeks_admin_writes_delete ON public.weeks FOR DELETE
  USING ((SELECT current_setting('request.jwt.claims.is_admin', true)) = 'true');
"""


def drop_duplicate_indexes(conn):
    # run drops concurrently outside transaction
    idxs = [
        'ix_picks_entry_id',
        'ix_picks_week_id'
    ]
    conn.autocommit = True
    with conn.cursor() as cur:
        for i in idxs:
            try:
                cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {i};")
                print(f'dropped index (if existed): {i}')
            except Exception as e:
                print(f'warning dropping index {i}: {e}')
    conn.autocommit = False


def verify_indexes(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename='picks';")
        rows = cur.fetchall()
        print('\nremaining picks indexes:')
        for r in rows:
            print(' -', r[0])


def apply_policy_sql(conn):
    with conn.cursor() as cur:
        cur.execute(POLICY_SQL)
    conn.commit()


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('Set DATABASE_URL in env')
        raise SystemExit(2)

    conn = parse_and_connect(database_url)
    try:
        print('Applying optimized RLS policies...')
        apply_policy_sql(conn)
        print('Dropping duplicate indexes concurrently...')
        drop_duplicate_indexes(conn)
        verify_indexes(conn)
    finally:
        conn.close()
