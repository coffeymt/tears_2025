from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class WeekBase(BaseModel):
    season_year: int
    week_number: int
    lock_time: Optional[datetime] = None
    ineligible_teams: Optional[List[str]] = []
    locked_games: Optional[List[int]] = []


class WeekCreate(WeekBase):
    pass


class WeekUpdate(BaseModel):
    lock_time: Optional[datetime] = None
    ineligible_teams: Optional[List[str]]
    locked_games: Optional[List[int]]
    is_current: Optional[bool]


class WeekOut(WeekBase):
    id: int
    is_current: bool

    class Config:
        orm_mode = True
