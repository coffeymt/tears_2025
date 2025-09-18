"""Verify that games.home_team_id/away_team_id and picks.team_id are populated after migration.

Usage:
$env:DATABASE_URL = 'postgresql://...'; python .\scripts\verify_team_fks.py
"""
import os
import psycopg2
from urllib.parse import urlparse


def run_check(database_url: str):
    conn = None
    try:
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            # manual parse to handle special characters in password
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

            conn = psycopg2.connect(**conn_params)
        else:
            conn = psycopg2.connect(database_url)
    except Exception:
        conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM games WHERE home_team_id IS NULL OR away_team_id IS NULL;")
            g_nulls = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM picks WHERE team_id IS NULL;")
            p_nulls = cur.fetchone()[0]
            print(f'games with null home/away team id: {g_nulls}')
            print(f'picks with null team_id: {p_nulls}')

            if g_nulls > 0:
                cur.execute("SELECT id, home_team_abbr, away_team_abbr FROM games WHERE home_team_id IS NULL OR away_team_id IS NULL LIMIT 20;")
                rows = cur.fetchall()
                print('\nSample problematic games (id, home_abbr, away_abbr):')
                for r in rows:
                    print(r)

            if p_nulls > 0:
                cur.execute("SELECT id, team_abbr, team_id FROM picks WHERE team_id IS NULL LIMIT 20;")
                rows = cur.fetchall()
                print('\nSample problematic picks (id, team_abbr, team_id):')
                for r in rows:
                    print(r)
    finally:
        conn.close()


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('Set DATABASE_URL in env')
        raise SystemExit(2)
    run_check(database_url)
