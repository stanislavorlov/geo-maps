from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select
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
