from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.history import get_history_matrix
from app.schemas.history_matrix import HistoryMatrixResponse

router = APIRouter()


@router.get("/api/history/matrix", response_model=HistoryMatrixResponse)
def history_matrix(season_year: int | None = None, db: Session = Depends(get_db)):
    """Return the season history matrix. Optional query param `season_year` to scope results."""
    data = get_history_matrix(db, season_year=season_year)
    return data
