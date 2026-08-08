from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import aliased
from geoalchemy2 import functions as geo_func
from .models import Location, Road
from models.geocode_model import ReverseGeocodeRequest

class RouteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query_route(
        self,
        start: ReverseGeocodeRequest,
        end: ReverseGeocodeRequest,
        buffer_degree: float = 0.01  # Default to ~1.1km instead of 5.5km
    ) -> list[tuple[Road, Location, Location]]:
        point_a_wkt = f"POINT({start.lng} {start.lat})"
        point_b_wkt = f"POINT({end.lng} {end.lat})"

        # Create a line connecting the start and end points
        route_line = geo_func.ST_MakeLine(
            geo_func.ST_GeomFromText(point_a_wkt, 4326),
            geo_func.ST_GeomFromText(point_b_wkt, 4326),
        )

        # Create aliases to join Location twice
        loc_from = aliased(Location)
        loc_to = aliased(Location)

        # ST_DWithin is index-accelerated and avoids constructing buffer geometries
        stmt = (
            select(Road, loc_from, loc_to)
            .join(loc_from, Road.from_id == loc_from.id)
            .join(loc_to, Road.to_id == loc_to.id)
            .where(
                and_(
                    geo_func.ST_DWithin(loc_from.geom, route_line, buffer_degree),
                    geo_func.ST_DWithin(loc_to.geom, route_line, buffer_degree)
                )
            )
        )

        result = await self.db.execute(stmt)
        # result contains rows of (Road, LocFrom, LocTo)
        return result.all()