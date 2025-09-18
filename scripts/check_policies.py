import os
import sqlalchemy as sa
from sqlalchemy import text
engine = sa.create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    for tbl in ['password_reset_tokens','alembic_version']:
        res = conn.execute(text("SELECT policyname FROM pg_policies WHERE schemaname='public' AND tablename=:t"), {'t':tbl}).fetchall()
        print(tbl, [r[0] for r in res])
