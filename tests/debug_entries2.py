import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from app.db import SessionLocal, engine
from app.models.base import Base
from app.models.week import Week
from fastapi.testclient import TestClient
import uuid

Base.metadata.create_all(bind=engine)

client = TestClient(app)

def run():
    db = SessionLocal()
    try:
        email = f"{uuid.uuid4()}@example.com"
        reg = client.post('/api/auth/register', json={'email': email, 'password': 'x'})
        print('reg', reg.status_code, reg.text)
        login = client.post('/api/auth/login', json={'email': email, 'password': 'x'})
        print('login', login.status_code, login.text)
        token = login.json().get('access_token')

        week = Week(season_year=2025, week_number=4)
        db.add(week)
        db.commit()
        db.refresh(week)

        r1 = client.post('/api/entries', json={'week_id': week.id, 'name': 'Alpha', 'picks': {'a':1}}, headers={'Authorization': f'Bearer {token}'})
        print('r1', r1.status_code, r1.text)

        r2 = client.post('/api/entries', json={'week_id': week.id, 'name': 'Alpha', 'picks': {'b':2}}, headers={'Authorization': f'Bearer {token}'})
        print('r2', r2.status_code, r2.text)
    finally:
        db.close()

if __name__ == '__main__':
    run()
