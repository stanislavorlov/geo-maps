import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from database.database import get_db
from database.location_repository import LocationRepository
from models.geocode_model import ReverseGeocodeRequest
from models.search_model import SearchRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["geocoding"])


@router.post("/search")
async def search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    # TODO: Implement search logic (e.g. forward geocoding or autocomplete)
    # Return a stub response for now
    return {
        "status": "success",
        "query": request.query,
        "results": [
            {"name": f"Stub result for '{request.query}'", "lat": 51.505, "lng": -0.09}
        ]
    }


@router.post("/reverse-geocode")
async def reverse_geocode(request: ReverseGeocodeRequest, db: AsyncSession = Depends(get_db)):
    repository = LocationRepository(db=db)

    lat, lng = request.lat, request.lng
    logger.info(f"Quering geocode position: {request}")

    location = await repository.get(lat, lng)

    if location:
        # Convert SQLAlchemy model to dict, ignoring internal state
        loc_dict = {c.name: getattr(location, c.name) for c in location.__table__.columns}
        logger.debug(f"Database result: {loc_dict}")
    else:
        logger.debug("Database result: None")

    # Determine a display name based on location data
    address = "Unknown Location"
    if location:
        if location.name:
            address = location.name
        elif location.description:
            address = location.description
        else:
            address = f"Unnamed location (ID: {location.id})"

    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "address": address,
        "location": {
            "id": location.id if location else None,
            "name": location.name if location else None,
            "description": location.description if location else None
        }
    }
