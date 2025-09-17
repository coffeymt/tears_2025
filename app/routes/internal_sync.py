from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Optional
from app.services.espn_client import fetch_games_for_week
from app.services.sync import transform_and_sync_games
from app.core.config import settings
from app.db import get_db

router = APIRouter(prefix="/internal", tags=["internal"])


def require_sync_token(x_internal_sync_token: Optional[str] = Header(None)):
    expected = getattr(settings, "INTERNAL_SYNC_TOKEN", None)
    if not expected or not x_internal_sync_token or x_internal_sync_token != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return True


@router.post("/sync-games/espn")
def sync_games_espn(year: int, week: int, db=Depends(get_db), _auth=Depends(require_sync_token)):
    """Trigger an immediate sync of ESPN games for a given year and week.

    Protected by a secret header `X-Internal-Sync-Token` configured in environment.
    """
    # Fetch raw data
    raw = fetch_games_for_week(year=year, week=week)
    # Transform and persist
    transform_and_sync_games(raw, year=year, week=week, db=db)
    return {"status": "ok"}
