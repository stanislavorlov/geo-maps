from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from .database import Base

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    
    # Store geographical coordinates (longitude, latitude)
    # Using SRID 4326 (WGS 84) which is standard for GPS
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
