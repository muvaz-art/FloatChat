# Database models for PostgreSQL + PostGIS integration
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FloatModel(Base):
    __tablename__ = "floats"
    float_id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    max_depth = Column(Float, nullable=False)
    region = Column(String(50))
