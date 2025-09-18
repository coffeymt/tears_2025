"""
Run EXPLAIN ANALYZE on the history matrix query against a Postgres (Supabase) database.

Usage (PowerShell):
$env:DATABASE_URL = "postgresql://user:pass@host:5432/dbname";
python .\scripts\run_explain_history.py --year 2025 --out .\\.taskmaster\\reports\\history_matrix_explain.txt

Requirements:
- Python 3.8+
- Install dependencies: `pip install psycopg2-binary`

Notes:
- The script reads SQL template from `.taskmaster/reports/history_matrix_explain.sql` and substitutes the year.
- It runs `EXPLAIN (ANALYZE, BUFFERS, VERBOSE)` and writes the formatted output to the specified file.

"""
import os
import argparse
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_TEMPLATE_PATH = os.path.join(ROOT, '.taskmaster', 'reports', 'history_matrix_explain.sql')


def load_sql_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def run_explain(database_url: str, sql: str, out_path: str):
    # Connect and run EXPLAIN ANALYZE.
    # DATABASE_URL may contain unencoded special characters; parse manually to avoid DSN parsing errors.
    conn = None
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        # split on last '@' so passwords with '@' are handled
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
                # remove any leading scheme if present
                conn_params['user'] = user
            if password:
                conn_params['password'] = password
            if host:
                conn_params['host'] = host
            if port:
                try:
                    conn_params['port'] = int(port)
                except Exception:
                    # leave as string; psycopg2 will handle if valid
                    conn_params['port'] = port

            conn = psycopg2.connect(**conn_params)
        except Exception:
            # fallback to direct connect attempt
            conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE) {sql}"
            cur.execute(explain_sql)
            rows = cur.fetchall()
            # cur.fetchall() returns list of one-column tuples where the column is the plan text
            plan_lines = [r[0] for r in rows]
            with open(out_path, 'w', encoding='utf-8') as out:
                out.write('\n'.join(plan_lines))
    finally:
        conn.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--year', type=int, required=True, help='Season year to profile (e.g., 2025)')
    p.add_argument('--out', type=str, default=os.path.join(ROOT, '.taskmaster', 'reports', 'history_matrix_explain.txt'), help='Output file for the explain plan')
    args = p.parse_args()

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('ERROR: Set the DATABASE_URL environment variable to your Supabase Postgres connection string.')
        raise SystemExit(2)

    sql_template = load_sql_template(SQL_TEMPLATE_PATH)
    sql = sql_template.replace('{{YEAR}}', str(args.year))

    print(f'Running EXPLAIN ANALYZE for year {args.year} against {database_url.split("@")[-1]}...')
    run_explain(database_url, sql, args.out)
    print(f'Explain plan written to: {args.out}')
