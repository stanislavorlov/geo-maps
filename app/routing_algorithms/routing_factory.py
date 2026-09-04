from models.search_model import RouteRequest
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm
from routing_algorithms.dijkstra_routing import DijkstraRoutingAlgorithm
from routing_algorithms.astar_routing import AStarRoutingAlgorithm


def get_routing_algorithm(request: RouteRequest) -> AbstractRoutingAlgorithm:
    match request.routeType:
        case "dijkstra":
            return DijkstraRoutingAlgorithm()
        case "astar":
            return AStarRoutingAlgorithm()
        case _:
            raise NotImplementedError(f"Route type '{request.routeType}' is not supported")