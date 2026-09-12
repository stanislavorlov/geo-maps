from sqlalchemy import Column, Integer, String, Float, BigInteger, JSON, UniqueConstraint
from geoalchemy2 import Geometry
from .database import Base

class Location(Base):
    __tablename__ = 'locations'

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    
    # Store geographical coordinates (longitude, latitude)
    # Using SRID 4326 (WGS 84) which is standard for GPS
    geom = Column(Geometry(geometry_type='POINT', srid=4326))

class Road(Base):
    __tablename__ = 'roads'
    __table_args__ = (
        UniqueConstraint('from_id', 'to_id', 'road_type', name='uq_roads_from_to'),
    )

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(BigInteger, index=True)
    to_id = Column(BigInteger, index=True)
    name = Column(String, nullable=True, index=True)
    distance = Column(Float)
    """distance in meters"""
    speed = Column(Float, nullable=True)
    """speed limit in mph"""
    road_type = Column(String, index=True)
    tags = Column(JSON, nullable=True)

