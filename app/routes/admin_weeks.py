from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db import get_db
from app.routes.auth import require_admin
from app.services.finalize import finalize_week_scores, FinalizeError
from app.schemas.finalize import FinalizeWeekPayload

router = APIRouter(prefix="/api/admin/weeks", tags=["admin_weeks"])


@router.post("/{week_id}/finalize-scores", status_code=200)
def finalize_week(week_id: int, payload: FinalizeWeekPayload, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Admin endpoint to finalize games for a week and resolve picks.

    Payload format is intentionally flexible for now; the service will validate required fields.
    Example payload: {"games": [{"game_id": 1, "home_score": 21, "away_score": 14}, ...]}
    """
    try:
        # Use Pydantic v2 API to avoid deprecation warnings from .dict()
        result = finalize_week_scores(db, week_id, payload.model_dump())
    except FinalizeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
