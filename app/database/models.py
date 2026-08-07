from sqlalchemy import Column, Integer, String, Float, BigInteger
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

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(BigInteger, index=True)
    to_id = Column(BigInteger, index=True)
    distance = Column(Float)
    speed = Column(Float)
    road_type = Column(String, index=True)
