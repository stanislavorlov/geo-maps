from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select
import networkx as nx
from geoalchemy2 import functions as geo_func
from models.geocode_model import ReverseGeocodeRequest
from .models import Location

class LocationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, lat: float, lng: float) -> Location | None:
        # Note: PostGIS expects longitude (X) before latitude (Y)
        point = f"SRID=4326;POINT({lng} {lat})"
        
        # Create a query to find the nearest location.
        # The distance_centroid method in GeoAlchemy2 uses the PostGIS `<->` operator,
        # which is highly optimized for nearest-neighbor searches using the GiST index.
        query = (
            select(Location)
            .order_by(Location.geom.distance_centroid(point))
            .limit(1)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def query_route(
        self, 
        start: ReverseGeocodeRequest, 
        end: ReverseGeocodeRequest,
        buffer_degree: float = 0.01  # Default to ~1.1km instead of 5.5km
    ) -> list[Location]:
        point_a_wkt = f"POINT({start.lng} {start.lat})"
        point_b_wkt = f"POINT({end.lng} {end.lat})"

        # Create a line connecting the start and end points
        route_line = geo_func.ST_MakeLine(
            geo_func.ST_GeomFromText(point_a_wkt, 4326),
            geo_func.ST_GeomFromText(point_b_wkt, 4326),
        )

        # ST_DWithin is index-accelerated and avoids constructing buffer geometries
        stmt = select(Location).where(
            geo_func.ST_DWithin(
                Location.geom,
                route_line,
                buffer_degree
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()