from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List, Optional
from datetime import datetime


class CurrentWeekInfo(BaseModel):
    week_id: Optional[int]
    week_number: Optional[int]
    lock_time: Optional[datetime]
    countdown_seconds: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class EntryPick(BaseModel):
    team_id: Optional[int]
    team_abbr: Optional[str]
    team_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class EntrySummary(BaseModel):
    id: int
    name: str
    is_eliminated: bool
    current_pick: Optional[EntryPick]

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    user_id: int
    entries: List[EntrySummary]
    current_week: Optional[CurrentWeekInfo]

    model_config = ConfigDict(from_attributes=True)
