import logging

import database.models
from fastapi import APIRouter, Depends
from geoalchemy2.shape import to_shape
from sqlalchemy.ext.asyncio.session import AsyncSession

from database.database import get_db
from database.route_repository import RouteRepository
from models.search_model import RouteRequest
from routing_algorithms.dijkstra_routing import shortest_path_map
from routing_algorithms.utils import find_nearest_location

logger = logging.getLogger(__name__)

DEFAULT_LONDON_SPEED = 30  # mph

router = APIRouter(prefix="/api", tags=["directions"])


@router.post("/find_route")
async def find_route(request: RouteRequest, db: AsyncSession = Depends(get_db)):
    repository = RouteRepository(db=db)

    query_result = await repository.query_route(request.from_, request.to)

    logger.info(f"Query result count: {len(query_result)}")

    '''
    TODO:
    Database already returns a set of points between 2 coordinates (it should also respect roads)
    Based on returned dataset, app should build a graph and apply some algorithm (Dijkstra's algorithm or A*) for finding routes
    Graph should involve the roads (edges) as well, so need to find out on how to query those as well
    Based on algorithm result, return the shortest path
    '''

    # Collect the unique graph nodes returned by the query
    locations: set[database.models.Location] = set()
    for _road, loc_from, loc_to in query_result:
        locations.add(loc_from)
        locations.add(loc_to)

    # Snap request coordinates to the nearest graph node.
    # An exact coordinate match will almost never happen for a user click,
    # so we pick the closest Location instead.
    location_from = find_nearest_location(locations, request.from_.lat, request.from_.lng)
    location_to = find_nearest_location(locations, request.to.lat, request.to.lng)

    if location_from is None or location_to is None:
        logger.warning("No graph nodes found near the requested coordinates")
        return {"status": "error", "message": "No roads found near the requested points"}

    logger.info(f"Location from {location_from.id} to {location_to.id}")

    result: list[database.models.Road] = shortest_path_map(query_result, location_from, location_to)

    if not result:
        logger.warning("No path found between the requested points")
        return {"status": "error", "message": "No route found between the requested points"}

    # id -> (loc_from, loc_to) so the path can be turned back into coordinates
    edges_by_road_id = {road.id: (loc_from, loc_to) for road, loc_from, loc_to in query_result}

    output = []
    total_distance = 0.0
    total_time = 0.0
    for road in result:
        loc_from, loc_to = edges_by_road_id[road.id]

        if not output:
            output.append([to_shape(loc_from.geom).y, to_shape(loc_from.geom).x])
        # Only append the far end - the near end is the previous edge's far end
        output.append([to_shape(loc_to.geom).y, to_shape(loc_to.geom).x])

        total_distance += road.distance
        #'road_type': road.road_type
        total_time += road.distance / (road.speed if road.speed else DEFAULT_LONDON_SPEED)

    return {
        "status": "success",
        "distance": total_distance,     # in meters
        "time": total_time,
        "path": output,
    }
