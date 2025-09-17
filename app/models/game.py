from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    home_team_abbr = Column(String, nullable=False, index=True)
    away_team_abbr = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="scheduled")
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
