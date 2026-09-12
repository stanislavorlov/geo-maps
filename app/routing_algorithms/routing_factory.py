from models.search_model import RouteRequest
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm
from routing_algorithms.dijkstra_routing import DijkstraRoutingAlgorithm
from routing_algorithms.astar_routing import AStarRoutingAlgorithm
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService


def get_routing_algorithm(
    request: RouteRequest,
    speed_limit_service: SpeedLimitService,
    travel_time_service: TravelTimeService
) -> AbstractRoutingAlgorithm:
    match request.routeType:
        case "dijkstra":
            return DijkstraRoutingAlgorithm(
                speed_limit_service=speed_limit_service,
                travel_time_service=travel_time_service
            )
        case "astar":
            return AStarRoutingAlgorithm(
                speed_limit_service=speed_limit_service,
                travel_time_service=travel_time_service
            )
        case _:
            raise NotImplementedError(f"Route type '{request.routeType}' is not supported")