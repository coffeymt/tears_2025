"""
Apply SQL statements from scripts/add_indexes_history.sql to the target DATABASE_URL.

Usage:
$env:DATABASE_URL = "postgresql://..."
python .\scripts\apply_indexes.py
"""
import os
from urllib.parse import urlparse
import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_PATH = os.path.join(ROOT, 'scripts', 'add_indexes_history.sql')


def load_sql(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def run_sql(database_url: str, sql: str):
    # simple execution of the SQL file; Postgres will ignore IF NOT EXISTS in CREATE INDEX
    conn = None
    try:
        # Handle DATABASE_URL with unencoded special characters by parsing manually
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            try:
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

                # host_part is like host:port/dbname or host/dbname
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

                conn = psycopg2.connect(**conn_params)
            except Exception:
                # fallback to DSN style connect
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)

        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('Set DATABASE_URL in env')
        raise SystemExit(2)
    sql = load_sql(SQL_PATH)
    print('Applying index SQL to', database_url.split('@')[-1])
    run_sql(database_url, sql)
    print('Done')
