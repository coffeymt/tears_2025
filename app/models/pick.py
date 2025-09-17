from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, UniqueConstraint
from app.models.base import Base
import datetime as _dt


class Pick(Base):
    __tablename__ = "picks"
    __table_args__ = (UniqueConstraint('entry_id', 'week_id', name='uq_picks_entry_week'),)

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False, index=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False, index=True)
    team_id = Column(Integer, nullable=False, index=True)
    result = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc))
    updated_at = Column(DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc))
