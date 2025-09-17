from fastapi import FastAPI

from app.routes import auth as auth_router
from app.routes import password_reset as password_reset_router
from app.routes import weeks as weeks_router
from app.routes import internal_sync as internal_sync_router
from app.routes import entries as entries_router
from app.routes import picks as picks_router
from app.routes import admin_weeks as admin_weeks_router


app = FastAPI(title="Tears 2025 API")


@app.get("/api/health")
async def health():
    """Health endpoint used by CI and local checks."""
    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(password_reset_router.router)
app.include_router(weeks_router.router)
app.include_router(internal_sync_router.router)
app.include_router(entries_router.router)
app.include_router(picks_router.router)
app.include_router(admin_weeks_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
