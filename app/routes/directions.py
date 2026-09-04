import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from database.database import get_db
from database.graph_repository import GraphRepository
from models.search_model import RouteRequest
from routing_algorithms.routing_factory import get_routing_algorithm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["directions"])


@router.post("/find_route")
async def find_route(request: RouteRequest, db: AsyncSession = Depends(get_db)):
    repository = GraphRepository(db=db)
    route_graph = await repository.query_route_graph(request.from_, request.to)

    logger.info(f"Fetched graph: {route_graph.data_stats()}")

    node_from = route_graph.find_nearest_node(request.from_.lat, request.from_.lng)
    node_to = route_graph.find_nearest_node(request.to.lat, request.to.lng)

    if node_from is None or node_to is None:
        logger.warning("No graph nodes found near the requested coordinates")
        return {"status": "error", "message": "No roads found near the requested points"}

    logger.info(f"Finding route from node {node_from.id} to node {node_to.id}")

    algorithm = get_routing_algorithm(request)
    result = algorithm.find_route(route_graph, node_from, node_to)

    if not result.found:
        logger.warning("No path found between the requested points")
        return {"status": "error", "message": "No route found between the requested points"}

    return {
        "status": "success",
        "distance": result.distance,     # in meters
        "time": result.time,
        "path": result.path,
    }
