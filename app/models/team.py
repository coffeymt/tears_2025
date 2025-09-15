from sqlalchemy import Column, Integer, String
from app.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    abbreviation = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    conference = Column(String, nullable=True)
    division = Column(String, nullable=True)
