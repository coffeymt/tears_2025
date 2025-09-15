from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy import JSON
from app.models.base import Base
import json


class Week(Base):
    __tablename__ = "weeks"

    id = Column(Integer, primary_key=True, index=True)
    season_year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)
    lock_time = Column(DateTime, nullable=True)
    # Use JSON column so SQLAlchemy maps to Python lists/dicts automatically
    ineligible_teams = Column(JSON, nullable=True)
    locked_games = Column(JSON, nullable=True)

    def get_ineligible_teams(self):
        # Return a Python list (never None to simplify usage)
        return self.ineligible_teams or []

    def set_ineligible_teams(self, lst):
        self.ineligible_teams = lst

    def get_locked_games(self):
        return self.locked_games or []

    def set_locked_games(self, lst):
        self.locked_games = lst
