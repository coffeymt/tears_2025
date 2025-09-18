"""Run the dev RLS SQL script and verify policy presence for key tables.

Usage:
$env:DATABASE_URL='postgresql://...'; python .\scripts\apply_rls_dev.py
"""
import os
import psycopg2


def parse_and_connect(database_url: str):
    # robust connect like other scripts to handle special chars
    conn = None
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
            conn = psycopg2.connect(**conn_params)
        except Exception:
            conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(database_url)
    return conn


def run_script(conn, path):
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def verify_policies(conn, tables):
    with conn.cursor() as cur:
        for t in tables:
            cur.execute("SELECT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename=%s);", (t,))
            exists = cur.fetchone()[0]
            print(f'table public.{t} has policies: {exists}')


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('Set DATABASE_URL in env')
        raise SystemExit(2)

    conn = parse_and_connect(database_url)
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'enable_rls_dev.sql')
        print('Applying RLS dev script...')
        run_script(conn, script_path)
        print('Verifying policies...')
        verify_policies(conn, ['entries', 'picks', 'users', 'teams', 'games', 'weeks'])
    finally:
        conn.close()
