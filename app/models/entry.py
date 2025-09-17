from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class Entry(Base):
    __tablename__ = "entries"
    # Enforce unique entry name per user per season
    __table_args__ = (UniqueConstraint('user_id', 'season_year', 'name', name='uq_entries_user_season_name'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False, index=True)
    # human-friendly entry name (e.g., "My Squad")
    name = Column(String, nullable=False, index=True)
    # derived from the associated Week at creation time
    season_year = Column(Integer, nullable=False, index=True)
    picks = Column(JSON, nullable=False)  # list/dict of picks
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    week = relationship("Week")
