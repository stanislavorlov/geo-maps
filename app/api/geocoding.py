import logging
from fastapi import APIRouter, Depends
from database.location_repository import LocationRepository
from models.geocode_model import ReverseGeocodeRequest
from models.search_model import SearchRequest
from api.dependencies import get_location_repository
from services.geocode_service import GeocodeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["geocoding"])


@router.post("/search")
async def search(request: SearchRequest):
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
async def reverse_geocode(
    request: ReverseGeocodeRequest,
    repository: LocationRepository = Depends(get_location_repository),
):
    lat, lng = request.lat, request.lng
    logger.info(f"Quering geocode position: {request}")

    location = await repository.get(lat, lng)
    display_data = GeocodeService.get_location_display_data(location)

    logger.debug(f"Address: {display_data['address']}")

    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "address": display_data["address"],
        "location": {
            "id": display_data["id"],
            "name": display_data["name"],
        }
    }
