from pydantic import BaseModel
from typing import List


class GameScoreIn(BaseModel):
    game_id: int
    home_score: int
    away_score: int


class FinalizeWeekPayload(BaseModel):
    games: List[GameScoreIn]
