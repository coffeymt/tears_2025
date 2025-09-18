from pydantic import BaseModel
from typing import List, Optional


class EntryRow(BaseModel):
    entry_id: int
    entry_name: str
    picks: List[Optional[int]]


class HistoryMatrixResponse(BaseModel):
    weeks: List[int]
    entries: List[EntryRow]
from pydantic import BaseModel
from typing import List, Optional


class EntryRow(BaseModel):
    entry_id: int
    entry_name: str
    picks: List[Optional[int]]  # team_id per week index (0-based for week order)


class HistoryMatrixResponse(BaseModel):
    weeks: List[int]  # list of week_number in order
    entries: List[EntryRow]
