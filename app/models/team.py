from sqlalchemy import Column, Integer, String
from app.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    abbr = Column(String, nullable=False, unique=True, index=True)
