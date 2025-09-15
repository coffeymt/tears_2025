# Tears 2025 - Backend (FastAPI)

Quickstart (Windows PowerShell):

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run development server:

```powershell
uvicorn app.main:app --reload
```

4. Run tests:

```powershell
pytest -q
```

Database migrations (alembic)

1. Initialize the DB URL in `.env` (or set `DATABASE_URL` env var). By default the code uses a local SQLite `dev.db`.

2. Create migrations and apply (example using alembic):

```powershell
python -m alembic revision --autogenerate -m "create initial tables"
python -m alembic upgrade head
```

Alembic is configured to import `app.models` for autogeneration. If you change model locations, update `alembic/env.py` accordingly.

The health endpoint is available at `GET /api/health`.
