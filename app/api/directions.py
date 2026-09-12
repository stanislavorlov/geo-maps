import logging
from fastapi import APIRouter, Depends
from database.graph_repository import GraphRepository
from models.search_model import RouteRequest
from routing_algorithms.routing_factory import get_routing_algorithm
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService
from api.dependencies import (
    get_graph_repository,
    get_speed_limit_service,
    get_travel_time_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["directions"])


@router.post("/find_route")
async def find_route(
    request: RouteRequest,
    repository: GraphRepository = Depends(get_graph_repository),
    speed_limit_service: SpeedLimitService = Depends(get_speed_limit_service),
    travel_time_service: TravelTimeService = Depends(get_travel_time_service),
):
    route_graph = await repository.query_route_graph(request.travelMode, request.from_, request.to)

    logger.info(f"Fetched graph: {route_graph.data_stats()}")

    node_from = route_graph.find_nearest_node(request.from_.lat, request.from_.lng)
    node_to = route_graph.find_nearest_node(request.to.lat, request.to.lng)

    if node_from is None or node_to is None:
        logger.warning("No graph nodes found near the requested coordinates")
        return {"status": "error", "message": "No roads found near the requested points"}

    logger.info(f"Finding route from node {node_from.id} to node {node_to.id}")

    algorithm = get_routing_algorithm(request, speed_limit_service, travel_time_service)
    result = algorithm.find_route(route_graph, node_from, node_to, request.travelMode)

    if not result.found:
        logger.warning("No path found between the requested points")
        return {"status": "error", "message": "No route found between the requested points"}

    return {
        "status": "success",
        "distance": result.distance,     # in meters
        "time": result.time,
        "path": result.path,
        "execution_time": result.execution_time,
        "nodes_visited_count": result.nodes_visited_count,
        "visited_nodes": result.nodes_visited_count,
    }
